
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
    triton_meta={'signature': {'in_out_ptr0': '*fp32', 'in_out_ptr1': '*fp32', 'in_ptr0': '*i64', 'in_ptr1': '*bf16', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*bf16', 'out_ptr1': '*bf16', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0', 'mutated_arg_names': ['in_out_ptr0', 'in_out_ptr1'], 'optimize_mem': False, 'no_x_dim': True, 'num_load': 3, 'num_reduction': 2, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_embedding_mean_mul_pow_rsqrt_0(in_out_ptr0, in_out_ptr1, in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, out_ptr1, xnumel, rnumel):
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
    x0 = xindex
    r1 = rindex
    tmp0 = tl.load(in_ptr0 + (x0), None, eviction_policy='evict_last')
    tmp17 = tl.load(in_ptr2 + (0))
    tmp18 = tl.broadcast_to(tmp17, [RBLOCK])
    tmp23 = tl.load(in_ptr3 + (0))
    tmp24 = tl.broadcast_to(tmp23, [RBLOCK])
    tmp1 = tl.full([RBLOCK], 8192, tl.int32)
    tmp2 = tmp0 + tmp1
    tmp3 = tmp0 < 0
    tmp4 = tl.where(tmp3, tmp2, tmp0)
    tl.device_assert((0 <= tmp4) & (tmp4 < 8192), "index out of bounds: 0 <= tmp4 < 8192")
    tmp6 = tl.load(in_ptr1 + (r1 + 256*tmp4), None).to(tl.float32)
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp7 * tmp7
    tmp9 = tl.broadcast_to(tmp8, [RBLOCK])
    tmp11 = triton_helpers.promote_to_tensor(tl.sum(tmp9, 0))
    tmp12 = 256.0
    tmp13 = tmp11 / tmp12
    tmp14 = 0.0078125
    tmp15 = tmp13 + tmp14
    tmp16 = libdevice.rsqrt(tmp15)
    tmp19 = tmp18.to(tl.float32)
    tmp20 = tmp7 * tmp16
    tmp21 = tmp20.to(tl.float32)
    tmp22 = tmp19 * tmp21
    tmp25 = tmp24.to(tl.float32)
    tmp26 = tmp25 * tmp21
    tmp27 = tmp22 + tmp26
    tmp28 = tmp27.to(tl.float32)
    tmp29 = tmp28 * tmp28
    tmp30 = tl.broadcast_to(tmp29, [RBLOCK])
    tmp32 = triton_helpers.promote_to_tensor(tl.sum(tmp30, 0))
    tmp33 = tmp32 / tmp12
    tmp34 = tmp33 + tmp14
    tmp35 = libdevice.rsqrt(tmp34)
    tmp36 = tmp28 * tmp35
    tmp37 = tmp36.to(tl.float32)
    tl.store(out_ptr0 + (r1 + 256*x0), tmp6, None)
    tl.debug_barrier()
    tl.store(in_out_ptr0 + (x0), tmp16, None)
    tl.debug_barrier()
    tl.store(in_out_ptr1 + (x0), tmp35, None)
    tl.store(out_ptr1 + (r1 + 256*x0), tmp37, None)
