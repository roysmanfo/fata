from mitmproxy import http


STATUS_NO_CONTENT = 204
"""No content response code."""
STATUS_FORBIDDEN = 403
"""Forbidden response code."""

RES_NO_CONTENT = http.Response.make(
    STATUS_NO_CONTENT,
    b"",
    http.Headers([
        (b"Content-Type", b"application/json"),
        (b"X-Reason", b"Blocked by Fata"),
    ])
)


# request blocked by fata
RES_FORBIDDEN = http.Response.make(
    STATUS_FORBIDDEN,
    
    b"Blocked by Fata\n"
    b"\n\n" +
    b"Fata is a free and open-source adblocker.\n" +
    b"Please consider supporting us on GitHub.\n",
    
    http.Headers([
        (b"Content-Type", b"application/json"),
        (b"X-Reason", b"Blocked by Fata"),
    ]),

)


