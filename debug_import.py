try:
    from flask_session import FileSystemSessionInterface
    print("Found in flask_session (top level)")
except ImportError:
    print("Not found in flask_session (top level)")

try:
    from flask_session.sessions import FileSystemSessionInterface
    print("Found in flask_session.sessions")
except ImportError:
    print("Not found in flask_session.sessions")

try:
    from flask_session.filesystem import FileSystemSessionInterface
    print("Found in flask_session.filesystem")
except ImportError:
    print("Not found in flask_session.filesystem")
