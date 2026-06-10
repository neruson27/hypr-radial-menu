#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s [press|release|quit]\n", argv[0]);
        return 1;
    }
    
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket");
        return 1;
    }
    
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    
    // Create a socket path specific to the current user to avoid permission conflicts
    snprintf(addr.sun_path, sizeof(addr.sun_path), "/tmp/hypr-radial-menu-%d.sock", getuid());
    
    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        // If daemon is not running, fail silently so mouse clicks don't hang
        close(fd);
        return 0;
    }
    
    write(fd, argv[1], strlen(argv[1]));
    close(fd);
    return 0;
}
