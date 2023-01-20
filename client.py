import rcon

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('-p', '--port', type=int, default=25575)
    args = parser.parse_args()

    password = input('Password: ')
    
    client = rcon.RconClient(args.host, args.port, password)
    client.console()

if __name__ == '__main__':
    main()
