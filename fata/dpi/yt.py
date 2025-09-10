from mitmproxy import http
import json
import re

from fata.dpi.base import Inspector
from fata.utils import RES_NO_CONTENT


class YTInspector(Inspector):

    def __init__(self, aggressive = False):
        super().__init__(aggressive)

        # Patterns for ad-serving URLs that we can block entirely
        self.block_patterns = [
            r'googlesyndication\.com',
            r'googleadservices\.com', 
            r'doubleclick\.net',
            r'googletagmanager\.com',
            r'google-analytics\.com',
            r'youtube\.com/api/stats/ads',
            r'youtube\.com/ptracking',
            r'youtube\.com/youtubei/v1/log_event.*',
        ]
        self.compiled_block_patterns = [re.compile(p, re.IGNORECASE) for p in self.block_patterns]


        self.url_patterns = self.compiled_block_patterns
        self.url_patterns.extend(
            re.compile(p, re.IGNORECASE) for p in [
                r".*\.youtube\.com/.*"
                r".*\.googlevideo\.com/.*"
            ]
        )

    def inspect(self, flow: http.HTTPFlow) -> bool:
        self.current_flow = flow

        self.logger.log("[DPI][YT] inspecting %s", flow.request.pretty_url)
        # Block known ad requests entirely
        if self.should_block_request(flow):
            self.logger.info(f"[DPI][YT] detected blacklisted domain {flow.request.pretty_url}")
            flow.response = RES_NO_CONTENT
            return True
        

        if not 'youtube.com' in flow.request.pretty_host:
            return False

        if flow.response:
            # skip large responses
            
            # limit to 2MB
            # todo: this should not be hardcoded
            max_size = 2 * pow(1024, 2)
            
            if cl := flow.response.headers.get("Content-Length"):
                if int(cl) > max_size:
                    return False 

            # manual length calculation fallback
            if len(flow.response.content) > max_size:
                return False

            return self._inspect_response()

        return False

    def should_block_request(self, flow: http.HTTPFlow) -> bool:
        """check if request should be blocked entirely"""
        url = flow.request.pretty_url
        return any(pattern.search(url) for pattern in self.compiled_block_patterns)

    def process_html_response(self, content: str) -> tuple[str, bool]:
        """Remove ads from HTML responses"""
        modified = False
        original_content = content
        
        # Remove ad-related script tags
        content = re.sub(r'<script[^>]*>.*?googlesyndication.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<script[^>]*>.*?googletagmanager.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove ad containers
        content = re.sub(r'<div[^>]*class="[^"]*ad[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<div[^>]*id="[^"]*ad[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove YouTube-specific ad elements
        content = re.sub(r'<div[^>]*class="[^"]*ytd-display-ad[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<ytd-display-ad-renderer.*?</ytd-display-ad-renderer>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        modified = content != original_content
        return content, modified

    def process_youtube_api_response(self, content: str, url: str) -> tuple[str, bool]:
        """Process YouTube API responses and remove ad content"""
        try:
            data = json.loads(content)
            modified = False
            
            # Handle different YouTube API endpoints
            if 'player_response' in url or 'youtubei/v1/player' in url:
                modified = self.clean_player_response(data)
            elif 'youtubei/v1/browse' in url or 'youtubei/v1/search' in url:
                modified = self.clean_browse_response(data)
            elif 'youtubei/v1/next' in url:
                modified = self.clean_next_response(data)
            
            if modified:
                return json.dumps(data, separators=(',', ':')), True
            
        except (json.JSONDecodeError, Exception) as e:
            self.logger.debug(f"Error processing JSON response: {e}")
            
        return content, False
    
    def clean_player_response(self, data: dict) -> bool:
        """Remove ads from player response"""
        modified = False
        
        # Remove ad placements
        if 'adPlacements' in data:
            data['adPlacements'] = []
            modified = True
            
        if 'playerAds' in data:
            data['playerAds'] = []
            modified = True
            
        # Clean video details
        if 'videoDetails' in data:
            video_details = data['videoDetails']
            if 'isLive' not in video_details or not video_details['isLive']:
                # Remove ad-related metadata
                for ad_key in ['adSlots', 'adPlacements', 'playerAds']:
                    if ad_key in video_details:
                        del video_details[ad_key]
                        modified = True
        
        # Clean streaming data
        if 'streamingData' in data:
            streaming_data = data['streamingData']
            
            # Remove adaptive formats that might be ads
            if 'adaptiveFormats' in streaming_data:
                original_count = len(streaming_data['adaptiveFormats'])
                streaming_data['adaptiveFormats'] = [
                    fmt for fmt in streaming_data['adaptiveFormats']
                    if not self.is_ad_format(fmt)
                ]
                if len(streaming_data['adaptiveFormats']) != original_count:
                    modified = True
        
        # Remove ad-related playability status
        if 'playabilityStatus' in data:
            status = data['playabilityStatus']
            if 'errorScreen' in status:
                error_screen = status['errorScreen']
                if 'playerErrorMessageRenderer' in error_screen:
                    # Don't modify actual errors, only ad-related ones
                    pass
        
        return modified
    
    def clean_browse_response(self, data: dict) -> bool:
        """Remove ads from browse/search responses"""
        modified = False
        
        def clean_contents(contents):
            nonlocal modified
            if not isinstance(contents, list):
                return
                
            # Remove ad-related renderers
            original_length = len(contents)
            contents[:] = [
                item for item in contents
                if not self.is_ad_renderer(item)
            ]
            if len(contents) != original_length:
                modified = True
            
            # Recursively clean nested contents
            for item in contents:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if key == 'contents' and isinstance(value, list):
                            clean_contents(value)
        
        # Clean main contents
        if 'contents' in data:
            if isinstance(data['contents'], dict):
                for section_key in data['contents']:
                    section = data['contents'][section_key]
                    if isinstance(section, dict) and 'contents' in section:
                        clean_contents(section['contents'])
            elif isinstance(data['contents'], list):
                clean_contents(data['contents'])
        
        # Clean sidebar/secondary content
        if 'sidebar' in data and isinstance(data['sidebar'], dict):
            if 'playlistPanelRenderer' in data['sidebar']:
                panel = data['sidebar']['playlistPanelRenderer']
                if 'contents' in panel:
                    clean_contents(panel['contents'])
        
        return modified
    
    def clean_next_response(self, data: dict) -> bool:
        """Remove ads from 'next' video responses"""
        modified = False
        
        # Clean video details in next response
        if 'contents' in data:
            contents = data['contents']
            if 'twoColumnWatchNextResults' in contents:
                watch_next = contents['twoColumnWatchNextResults']
                
                # Clean secondary results (recommended videos)
                if 'secondaryResults' in watch_next:
                    secondary = watch_next['secondaryResults']
                    if 'secondaryResults' in secondary and 'results' in secondary['secondaryResults']:
                        results = secondary['secondaryResults']['results']
                        original_count = len(results)
                        results[:] = [r for r in results if not self.is_ad_renderer(r)]
                        if len(results) != original_count:
                            modified = True
        
        return modified
    
    def is_ad_renderer(self, item: dict) -> bool:
        """Check if a renderer item is an advertisement"""
        if not isinstance(item, dict):
            return False
            
        # Check for ad-specific renderer types
        ad_renderers = [
            'displayAdRenderer',
            'promotedVideoRenderer', 
            'adSlotRenderer',
            'carouselAdRenderer',
            'inFeedAdRenderer',
            'searchAdRenderer'
        ]
        
        for renderer in ad_renderers:
            if renderer in item:
                return True
        
        # Check for promoted content markers
        if 'promotedSparklesTextSearchRenderer' in item:
            return True
            
        # Check for ad badges in video renderers
        if 'videoRenderer' in item:
            video = item['videoRenderer']
            if 'badges' in video:
                for badge in video['badges']:
                    if 'metadataBadgeRenderer' in badge:
                        badge_text = badge['metadataBadgeRenderer'].get('label', '').lower()
                        if 'ad' in badge_text or 'sponsored' in badge_text:
                            return True
        
        return False
    
    def is_ad_format(self, format_info: dict) -> bool:
        """Check if a streaming format is ad-related"""
        if not isinstance(format_info, dict):
            return False
            
        # Check URL for ad indicators
        url = format_info.get('url', '')
        if any(term in url.lower() for term in ['oad=', 'ad_type=', 'adformat=']):
            return True
            
        # Check for very short durations (typical of some ad formats)
        if 'contentLength' in format_info:
            try:
                length = int(format_info['contentLength'])
                if length < 1000:  # Less than 1KB, likely ad metadata
                    return True
            except (ValueError, TypeError):
                pass
                
        return False

    def _inspect_response(self) -> bool:
        """handle responses and perform DPI filtering"""
        
        response = self.current_flow.response
        request = self.current_flow.request

        # Only process YouTube and Google responses
        if not any(domain in request.pretty_host 
                for domain in ['youtube.com', 'googlevideo.com', 'google.com']):
            return False
        
        content_type = response.headers.get("content-type", "").lower()
        
        try:
            # Process JSON API responses (most important for YouTube)
            if "application/json" in content_type:
                content = response.get_text()
                if content:
                    new_content, modified = self.process_youtube_api_response(content, request.pretty_url)
                    if modified:
                        response.set_text(new_content)
                        self.logger.info(f"Modified JSON response for {request.path}")
                        return True

            # Process HTML responses
            elif "text/html" in content_type:
                content = response.get_text()
                if content:
                    new_content, modified = self.process_html_response(content)
                    if modified:
                        response.set_text(new_content)
                        self.logger.info(f"Modified HTML response for {request.path}")
                        return True

            # Process JavaScript responses
            elif any(js_type in content_type for js_type in ["application/javascript", "text/javascript"]):
                content = response.get_text()
                if content and any(term in content.lower() for term in ['advertisement', 'googlesyndication', 'adsbygoogle']):
                    # Simple approach: comment out ad-related JS
                    modified_content = re.sub(r'(.*googlesyndication.*)', r'// \1', content, flags=re.MULTILINE)
                    modified_content = re.sub(r'(.*adsbygoogle.*)', r'// \1', modified_content, flags=re.MULTILINE)
                    if modified_content != content:
                        response.set_text(modified_content)
                        self.logger.info(f"Modified JS response for {request.path}")
                        return True
                    
        except Exception as e:
            self.logger.error(f"Error processing response from {request.pretty_url}: {e}")

        return False

