APP_NAME = "Fastrim"
ORG_NAME = "Fastrim"

IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".jfif",
    ".png",
    ".gif",
    ".bmp",
    ".dib",
    ".webp",
    ".tif",
    ".tiff",
    ".ico",
    ".tga",
    ".ppm",
    ".pgm",
    ".pbm",
    ".heic",
    ".heif",
}

OPEN_FILTER = (
    "Images ("
    "*.jpg *.jpeg *.jfif *.png *.gif *.bmp *.webp *.tif *.tiff "
    "*.ico *.tga *.heic *.heif"
    ");;All files (*.*)"
)

ZOOM_CHOICES = [
    ("Fit", "fit"),
    ("25%", "25"),
    ("50%", "50"),
    ("75%", "75"),
    ("100%", "100"),
    ("150%", "150"),
    ("200%", "200"),
    ("300%", "300"),
    ("400%", "400"),
]

LONG_SIDE_CHOICES = [640, 800, 1024, 1280, 1600, 1920, 2048, 2560, 3840]

ASPECT_CHOICES = ["1:1", "3:2", "2:3", "4:3", "3:4", "16:9", "9:16", "5:4", "4:5"]

PRESET_SEQ = "seq"
PRESET_DATETIME = "datetime"
PRESET_SEQ_ONLY = "seq_only"
