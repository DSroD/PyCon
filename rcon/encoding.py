from models.server import Server


def encoding(game: Server.Type):
    match game:
        case Server.Type.SOURCE_SERVER: return "ascii"
        case Server.Type.MINECRAFT_SERVER: return "utf-8"
