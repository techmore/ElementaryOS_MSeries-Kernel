#include "vk_queue.c"
#include <stdio.h>
void _vk_device_report_lost(struct vk_device *device) { device->_lost.reported = true; }
struct test_state { struct vk_queue queue; struct vk_device dev; struct list_head pending; VkResult result; };
static int drain_thread(void *arg) { struct test_state *t = arg; t->result = vk_queue_drain(&t->queue); return 0; }
static int run_case(bool lose) {
   struct test_state t = {0};
   t.queue.base.device = &t.dev;
   list_inithead(&t.queue.submit.submits);
   list_addtail(&t.pending, &t.queue.submit.submits);
   mtx_init(&t.queue.submit.mutex, mtx_plain);
   cnd_init(&t.queue.submit.pop);
   thrd_t thread;
   if (thrd_create(&thread, drain_thread, &t) != thrd_success) return 1;
   struct timespec delay = {.tv_nsec = lose ? 30000000 : 250000000}; thrd_sleep(&delay, NULL);
   if (lose) {
      p_atomic_set(&t.dev._lost.lost, 1);
   } else {
      mtx_lock(&t.queue.submit.mutex);
      list_del(&t.pending);
      cnd_broadcast(&t.queue.submit.pop);
      mtx_unlock(&t.queue.submit.mutex);
   }
   thrd_join(thread, NULL);
   cnd_destroy(&t.queue.submit.pop); mtx_destroy(&t.queue.submit.mutex);
   return t.result != (lose ? VK_ERROR_DEVICE_LOST : VK_SUCCESS);
}
int main(void) { int a = run_case(false), b = run_case(true); printf("healthy=%s loss_without_signal=%s\n", a ? "FAIL" : "PASS", b ? "FAIL" : "PASS"); return a || b; }
