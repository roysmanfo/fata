import time
import logging
from pathlib import Path

from adblock import Engine, FilterSet
from mitmproxy import http

from fata.dpi import DPI
from fata.utils import RES_FORBIDDEN


filename = str(Path(__file__).parent.parent / "fata.log")




class Shield:
    def __init__(self, optimize: bool = True, debug: bool = False, aggressive: bool = True):
        start = time.time()
        LISTS = Path(__file__).parent.parent / "lists"

        self.filter_set = FilterSet(debug=debug)
        self.filter_set.add_filters(self._read_dir(LISTS, recursive=True))
        
        self.engine = Engine(self.filter_set, optimize=optimize)
        
        self.logger = logging.getLogger("fata")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.FileHandler(filename))
        self.logger.debug(f"[*] logging to {filename}")
        
        if debug:
            # print to stdout, ignore where self.logger points
            print(f"[*] finished loading filter lists in {time.time() - start:.2f} seconds")

        self.inspector = DPI(aggressive=aggressive, debug=debug)

    def analyze(self, flow: http.HTTPFlow):
        url = flow.request.url
        ref = flow.request.headers.get("Referer", flow.request.host)
        resource_type = flow.request.headers.get("Content-Type", "other")

        # logger.debug(f"just youtube: {self.yt_adblock._is_youtube_site(flow)}")
        # logger.debug(f"youtube player api: {self.yt_adblock._is_youtube_player_api(flow)}")
        
        if self.inspector.inspect(flow):
            self.logger.info("[DPI] blocked %s", flow.request.pretty_url)
            return

        # if self.yt_adblock.is_youtube_player_api(flow):
        #     self.yt_adblock.inspect(flow)
        #     return

        result = self.engine.check_network_urls(url, ref, resource_type)

        if result.matched:

            res = RES_FORBIDDEN
            res.set_content(
                b"Blocked by Fata\n" +
                b"------------------------\n" +
                b"\nmatches: " + str(result.filter).encode("utf-8") +
                b"\nhost: " + flow.request.pretty_host.encode("utf-8") +
                b"\nimportant: " + str(result.important).encode("utf-8") +
                b"\nredirect: " + str(result.redirect).encode("utf-8") +
                b"\nredirect_type: " + str(result.redirect_type).encode("utf-8") +
                b"\nerror: " + str(result.error).encode("utf-8") +
                b"\n\n" +
                b"Fata is a free and open-source adblocker.\n" +
                b"Please consider supporting us on GitHub.\n"
            )
            flow.response = res

            self.logger.info("blocked %s", flow.request.pretty_url)

    def _read_list(self, file_path: str | Path) -> list[str]:
        with open(file_path, 'r', encoding="utf-8") as file:
            return file.read().splitlines()

    def _read_dir(self, dir_path: str | Path, recursive: bool = False) -> list[str]:
        file_list = []
        for file in Path(dir_path).iterdir():
            if file.is_file() and file.suffix == ".txt":
                file_list.extend(self._read_list(file))
            elif file.is_dir() and recursive and not file.name == "test":
                file_list.extend(self._read_dir(file, recursive=True))
        return file_list


