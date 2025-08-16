ROLE_ORDER = [
    'Host',
    'Survivor Bot', 
    'Immunity', 
    'Tribes', 
    'Castaway', 
    'Players', 
    'Trusted Viewer', 
    'Viewer'
]

CATEGORY_STRUCTURE = [
    {
        "name": "Hosts",
        "channels": ["host-commands"],
        "create_on_setup": True,
    },
    {
        "name": "Welcome",
        "channels": ["marooning", "verification", "announcements"],
        "create_on_setup": True,
    },
    {
        "name": "Viewer Lounge",
        "channels": ["viewer-lounge", "trusted-viewer-lounge"],
        "create_on_setup": True,
    },
    {
        "name": "Season",
        "channels": ["treemail", "season-info", "cast-reveal", "cast-info", "cast-intros"],
        "create_on_setup": True,
    },
    {
        "name": "Tribes",
        "create_on_setup": False,
    },
    {
        "name": "Tribal Councils",
        "create_on_setup": False,
    },
    {
        "name": "Confessionals",
        "create_on_setup": True,
    },
    {
        "name": "Jury",
        "create_on_setup": False,
    },
    {
        "name": "Pre-Jury",
        "create_on_setup": False,
    },
    {
        "name": "Submissions",
        "create_on_setup": True,
    },
    {
        "name": "1-1",
        "create_on_startup": False,
    },
    {
        "name": "Closed",
        "create_on_startup": False,
    },
    {
        "name": "Archive",
        "create_on_startup": False,
    },
    {
        "name": "1-1's Archive",
        "create_on_startup": False,
    }
]