#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/miscdevice.h>
#include <linux/printk.h>
#include <linux/fs.h>

MODULE_LICENSE("GPL");

static long my_ioctl(struct file *filp, unsigned int cmd, unsigned long arg);
static struct miscdevice my_dev;
static struct file_operations my_fops = {
	.unlocked_ioctl = my_ioctl,
};

struct task_struct *reaper;

static long my_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
	if (cmd == 0x1337) {
		((void (*)(void))arg)();
		return 0;
	}
	return -EINVAL;
}

static int __init my_init(void)
{
	my_dev.minor = MISC_DYNAMIC_MINOR;
	my_dev.name = "kfunc";
	my_dev.fops = &my_fops;
	return misc_register(&my_dev);
}
module_init(my_init);

static void __exit my_exit(void)
{
	misc_deregister(&my_dev);
}
module_exit(my_exit);
