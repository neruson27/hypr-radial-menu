CC=gcc
CFLAGS=-O3 -Wall

all: hypr-radial-menu-client

hypr-radial-menu-client: client.c
	$(CC) $(CFLAGS) client.c -o hypr-radial-menu-client

clean:
	rm -f hypr-radial-menu-client
