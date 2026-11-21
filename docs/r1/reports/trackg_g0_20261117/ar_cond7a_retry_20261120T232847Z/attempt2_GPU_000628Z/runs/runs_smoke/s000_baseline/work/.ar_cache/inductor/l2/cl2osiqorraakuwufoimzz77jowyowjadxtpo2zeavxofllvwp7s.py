
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
    triton_meta={'signature': {'in_out_ptr0': '*bf16', 'in_ptr0': '*bf16', 'in_ptr1': '*bf16', 'in_ptr2': '*bf16', 'in_ptr3': '*bf16', 'in_ptr4': '*fp32', 'in_ptr5': '*fp32', 'in_ptr6': '*bf16', 'in_ptr7': '*bf16', 'in_ptr8': '*bf16', 'in_ptr9': '*fp32', 'in_ptr10': '*bf16', 'in_ptr11': '*bf16', 'out_ptr1': '*bf16', 'out_ptr2': '*fp32', 'out_ptr3': '*fp32', 'out_ptr4': '*fp32', 'out_ptr5': '*fp32', 'xnumel': 'i32', 'rnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=142, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_per_fused__to_copy_add_div_mul_pow_sum_view_16', 'mutated_arg_names': ['in_out_ptr0'], 'optimize_mem': True, 'no_x_dim': True, 'num_load': 13, 'num_reduction': 5, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False}
)
@triton.jit
def triton_per_fused__to_copy_add_div_mul_pow_sum_view_16(in_out_ptr0, in_ptr0, in_ptr1, in_ptr2, in_ptr3, in_ptr4, in_ptr5, in_ptr6, in_ptr7, in_ptr8, in_ptr9, in_ptr10, in_ptr11, out_ptr1, out_ptr2, out_ptr3, out_ptr4, out_ptr5, xnumel, rnumel):
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
    tmp0 = tl.load(in_out_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp1 = tl.load(in_ptr0 + (r1 + 256*x0), None).to(tl.float32)
    tmp3 = tl.load(in_ptr1 + (r1 + 256*x0), None).to(tl.float32)
    tmp6 = tl.load(in_ptr2 + (r1 + 256*x0), None).to(tl.float32)
    tmp12 = tl.load(in_ptr3 + (r1 + 256*x0), None).to(tl.float32)
    tmp13 = tl.load(in_ptr4 + (x0), None, eviction_policy='evict_last')
    tmp28 = tl.load(in_ptr5 + (2))
    tmp29 = tl.broadcast_to(tmp28, [RBLOCK])
    tmp32 = tl.load(in_ptr6 + (r1 + 256*x0), None).to(tl.float32)
    tmp33 = tl.load(in_ptr7 + (r1 + 256*x0), None).to(tl.float32)
    tmp35 = tl.load(in_ptr8 + (r1 + 256*x0), None).to(tl.float32)
    tmp37 = tl.load(in_ptr9 + (x0), None, eviction_policy='evict_last')
    tmp45 = tl.load(in_ptr10 + (r1 + 256*x0), None).to(tl.float32)
    tmp56 = tl.load(in_ptr11 + (r1 + 256*x0), None).to(tl.float32)
    tmp2 = tmp0 + tmp1
    tmp4 = tmp2 + tmp3
    tmp5 = tmp4.to(tl.float32)
    tmp7 = tmp6.to(tl.float32)
    tmp8 = tmp5 * tmp7
    tmp9 = tl.broadcast_to(tmp8, [RBLOCK])
    tmp11 = triton_helpers.promote_to_tensor(tl.sum(tmp9, 0))
    tmp14 = tmp5 * tmp13
    tmp15 = -0.5
    tmp16 = tmp11 * tmp15
    tmp17 = tmp13 * tmp13
    tmp18 = tmp17 * tmp13
    tmp19 = tmp16 * tmp18
    tmp20 = 0.00390625
    tmp21 = tmp19 * tmp20
    tmp22 = 2.0
    tmp23 = tmp7 * tmp22
    tmp24 = tmp21 * tmp23
    tmp25 = tmp14 + tmp24
    tmp26 = tmp25.to(tl.float32)
    tmp27 = tmp12 + tmp26
    tmp30 = tmp29.to(tl.float32)
    tmp31 = tmp27 * tmp30
    tmp34 = tmp32 + tmp33
    tmp36 = tmp35.to(tl.float32)
    tmp38 = tmp36 * tmp37
    tmp39 = tmp38.to(tl.float32)
    tmp40 = tmp34 * tmp39
    tmp41 = tmp40.to(tl.float32)
    tmp42 = tl.broadcast_to(tmp41, [RBLOCK])
    tmp44 = triton_helpers.promote_to_tensor(tl.sum(tmp42, 0))
    tmp46 = tmp34 * tmp45
    tmp47 = tmp46.to(tl.float32)
    tmp48 = tl.broadcast_to(tmp47, [RBLOCK])
    tmp50 = triton_helpers.promote_to_tensor(tl.sum(tmp48, 0))
    tmp51 = tmp27 * tmp39
    tmp52 = tmp51.to(tl.float32)
    tmp53 = tl.broadcast_to(tmp52, [RBLOCK])
    tmp55 = triton_helpers.promote_to_tensor(tl.sum(tmp53, 0))
    tmp57 = tmp27 * tmp56
    tmp58 = tmp57.to(tl.float32)
    tmp59 = tl.broadcast_to(tmp58, [RBLOCK])
    tmp61 = triton_helpers.promote_to_tensor(tl.sum(tmp59, 0))
    tl.store(in_out_ptr0 + (r1 + 256*x0), tmp27, None)
    tl.store(out_ptr1 + (r1 + 256*x0), tmp31, None)
    tl.store(out_ptr2 + (x0), tmp44, None)
    tl.store(out_ptr3 + (x0), tmp50, None)
    tl.store(out_ptr4 + (x0), tmp55, None)
    tl.store(out_ptr5 + (x0), tmp61, None)
