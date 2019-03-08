# coding=utf-8


class MIME(object):
    """
    mime列表
    """
    Json = "application/json;"
    Text = "text/plain; charset=utf-8"
    Form = "application/x-www-form-urlencoded"
    Multipart = "multipart/form-data"
    Html = "text/html; charset=utf-8"
    Css = "text/css; charset=utf-8"
    Javascript = "text/javascript; charset=utf-8"
    Gif = "image/gif"
    Png = "image/png"
    Jpeg = "image/jpeg"
    Bmp = "image/bmp"
    Wbp = "image/wbp"
    Icon = "image/x-icon"
    Svg = "image/svg+xml"
    Wav = "audio/wav"
    Ogg = "audio/ogg"
    Mpeg = "audio/mpeg"
    Midi = "audio/midi"
    Webm = "video/webm"
    Bin = "application/octet-stream"
    PPT = "application/vnd.mspowerpoint"
    Doc = "application/msword"
    Xls = "application/vnd.ms-excel"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    Xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    Docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XML = "application/xhtml+xml"
    PDF = "application/pdf"


Suffix_mime = {
    "json": MIME.Json,
    "html": MIME.Text,
    "txt": MIME.Text,
    "css": MIME.Css,
    "js": MIME.Javascript,
    "gif": MIME.Gif,
    "png": MIME.Png,
    "jpg": MIME.Jpeg,
    "jpeg": MIME.Jpeg,
    "bmp": MIME.Bmp,
    "wbp": MIME.Wbp,
    "ico": MIME.Icon,
    "svg": MIME.Svg,
    "wav": MIME.Wav,
    "ogg": MIME.Ogg,
    "webm": MIME.Webm,
    "mp3": MIME.Mpeg,
    "midi": MIME.Midi,
    "bin": MIME.Bin,
    "ppt": MIME.PPT,
    "pptx": MIME.PPTX,
    "doc": MIME.Doc,
    "docx": MIME.Docx,
    "xls": MIME.Xls,
    "xlsx": MIME.Xlsx,
    "xml": MIME.XML,
    "pdf": MIME.PDF
}
