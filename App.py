from Main import App, sys

if __name__ == '__main__':
    App.Start(
        load=sys.argv[1] if len(sys.argv) > 1 else ''
    )
