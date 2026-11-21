
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 32768, 'r': 256},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_out_ptr1': '*fp32', 'in_ptr0': '*fp32', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 5, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_mean_mul_pow_rsqrt_3(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, xnumel, rnumel):
    xnumel = 32768
    XBLOCK: tl.constexpr = 1
    rnumel = 256
    RBLOCK: tl.constexpr = 256
    xoffset = tl.program_id(0) * XBLOCK
    xindex = tl.full([1], xoffset, tl.int32)
    xmask = tl.full([RBLOCK], True, tl.int1)
    rindex = tl.arange(0, RBLOCK)[:]
    roffset = 0
    rmask = tl.full([RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [RBLOCK])
    tmp3 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp5 = tl.load(in_ptr2 + (x0), None, eviction_policy='evict_last')
    tmp9 = tl.load(in_ptr3 + (0))
    tmp10 = tl.broadcast_to(tmp9, [RBLOCK])
    tmp14 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tmp1.to(tl.float32)
    tmp4 = tmp3.to(tl.float32)
    tmp6 = tmp4 * tmp5
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp2 * tmp7
    tmp11 = tmp10.to(tl.float32)
    tmp12 = tmp11 * tmp7
    tmp13 = tmp8 + tmp12
    tmp15 = tmp13 + tmp14
    tmp16 = tmp15.to(tl.float32)
    tmp17 = tmp16 * tmp16
    tmp18 = tl.broadcast_to(tmp17, [RBLOCK])
    tmp20 = triton_helpers.promote_to_tensor(tl.sum(tmp18, 0))
    tmp21 = 256.0
    tmp22 = tmp20 / tmp21
    tmp23 = 0.0078125
    tmp24 = tmp22 + tmp23
    tmp25 = libdevice.rsqrt(tmp24)
    tmp26 = tmp16 * tmp25
    tmp27 = tmp26.to(tl.float32)
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp15, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp25, None)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp27, None)
