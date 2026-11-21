
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.persistent_reduction(
    size_hints={'x': 2, 'r': 64},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'out_ptr1': '*bf16', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 7), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_0', 'mutated_arg_names': ['in_ptr1', 'in_ptr2', 'out_ptr4', 'out_ptr5'], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 3, 'num_reduction': 1, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_lerp_linalg_vector_norm_mul_rsub_0(in_ptr0, in_ptr1, in_ptr2, out_ptr1, out_ptr4, out_ptr5, xnumel, rnumel, XBLOCK : tl.constexpr):
    xnumel = 2
    rnumel = 64
    RBLOCK: tl.constexpr = 64
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None]
    xmask = xindex < xnumel
    rindex = tl.arange(0, RBLOCK)[None, :]
    roffset = 0
    rmask = tl.full([XBLOCK, RBLOCK], True, tl.int1)
    r1 = rindex
    x0 = xindex
    tmp0 = tl.load(in_ptr0 + (0))
    tmp1 = tl.broadcast_to(tmp0, [XBLOCK, RBLOCK])
    tmp13 = tl.load(in_ptr1 + (r1 + 64*x0), xmask, other=0.0)
    tmp14 = tl.load(in_ptr2 + (r1 + 64*x0), xmask, other=0.0)
    tmp2 = tl_math.abs(tmp1)
    tmp3 = 0.5
    tmp4 = tmp2 >= tmp3
    tmp5 = 1.0
    tmp6 = tmp1 - tmp5
    tmp7 = tl.where(tmp4, tmp6, tmp1)
    tmp8 = tmp5 - tmp1
    tmp9 = tl_math.abs(tmp8)
    tmp10 = tmp9 >= tmp3
    tmp11 = tmp8 - tmp5
    tmp12 = tl.where(tmp10, tmp11, tmp8)
    tmp15 = tmp13 - tmp14
    tmp16 = tmp12 * tmp15
    tmp17 = tl.where(tmp10, tmp13, tmp14)
    tmp18 = tmp16 + tmp17
    tmp19 = tmp18 - tmp13
    tmp20 = tmp7 * tmp19
    tmp21 = tl.where(tmp4, tmp18, tmp13)
    tmp22 = tmp20 + tmp21
    tmp23 = tmp22.to(tl.float32)
    tmp24 = tmp23.to(tl.float32)
    tmp25 = tmp24 * tmp24
    tmp26 = tl.broadcast_to(tmp25, [XBLOCK, RBLOCK])
    tmp28 = tl.where(xmask, tmp26, 0)
    tmp29 = tl.sum(tmp28, 1)[:, None]
    tmp30 = libdevice.sqrt(tmp29)
    tmp31 = tmp30.to(tl.float32)
    tmp32 = 1.02
    tmp33 = tmp31 * tmp32
    tmp34 = 1e-06
    tmp35 = tmp33 + tmp34
    tmp36 = tmp23 / tmp35
    tl.store(out_ptr1 + (r1 + 64*x0), tmp36, xmask)
    tl.store(out_ptr4 + (r1 + 64*x0), tmp22, xmask)
    tl.store(out_ptr5 + (r1 + 64*x0), tmp18, xmask)
