🏝️ Discord Survivor Bot

A custom Discord bot designed to manage and enhance your Survivor-style games on Discord. It provides seamless integration with a database to handle seasons, tribes, and players, while automating channel setup and role management.
🚀 Features

    🔗 Slash Commands with Autocomplete
    Easily manage seasons, tribes, and players using intuitive slash commands.

    📦 Database Integration
    All game data — seasons, tribes, players — is stored and retrieved from a connected database.

    👥 Automatic Role Management
    New members are automatically added to the database and given the "Viewer" role.

    🎨 Color Customization
    Tribes and players can be assigned custom hex colors for styling and visibility.

    📁 Submission Channel Creation
    Automatically generates private channels for player submissions.

📋 Commands
/addseason <name> <number>

Add a new season to the database.
/listseasons

List all seasons currently registered.
/setseason <season>

Set one season as active (disables all others).
/addtribe <season> <tribe_name> <tribe_color>

Add a tribe with a custom color to a specific season.
/addplayer <season> <user> <display_name> [role_color] [tribe]

Register a player for a season and optionally assign them a tribe and color.
/createsubmissions <player>

Create private submission channels for a player or all players in the active season.
