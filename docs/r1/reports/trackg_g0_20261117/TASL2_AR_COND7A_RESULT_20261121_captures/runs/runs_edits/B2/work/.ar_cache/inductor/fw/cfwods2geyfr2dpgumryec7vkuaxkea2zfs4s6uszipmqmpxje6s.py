
import triton
import triton.language as tl
from triton.compiler.compiler import AttrsDescriptor

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.pointwise(
    size_hints={'x': 4}, 
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'in_ptr2': '*fp32', 'in_ptr3': '*fp32', 'out_ptr0': '*fp32', 'xnumel': 'i32'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=128, cc=89, major=8, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, warp_size=32), 'constants': {}, 'configs': [AttrsDescriptor.from_dict({'arg_properties': {'tt.divisibility': (0, 1, 2, 3, 4), 'tt.equal_to': ()}, 'cls': 'AttrsDescriptor'})]},
    inductor_meta={'autotune_hints': set(), 'kernel_name': 'triton_poi_fused_add_select_backward_22', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'num_load': 4, 'num_reduction': 0, 'backend_hash': 'E859E07B6B62AFA163C40CD3F96C46CB1FA6DF68D13FA0DF3E136DE6944A067E', 'are_deterministic_algorithms_enabled': True, 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False},
    min_elem_per_thread=0
)
@triton.jit
def triton_poi_fused_add_select_backward_22(in_ptr0, in_ptr1, in_ptr2, in_ptr3, out_ptr0, xnumel, XBLOCK : tl.constexpr):
    xnumel = 4
    xoffset = tl.program_id(0) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:]
    xmask = xindex < xnumel
    x0 = xindex
    tmp3 = tl.load(in_ptr0 + (0))
    tmp4 = tl.broadcast_to(tmp3, [XBLOCK])
    tmp9 = tl.load(in_ptr1 + (0))
    tmp10 = tl.broadcast_to(tmp9, [XBLOCK])
    tmp15 = tl.load(in_ptr2 + (0))
    tmp16 = tl.broadcast_to(tmp15, [XBLOCK])
    tmp21 = tl.load(in_ptr3 + (0))
    tmp22 = tl.broadcast_to(tmp21, [XBLOCK])
    tmp0 = x0
    tmp1 = tl.full([1], 3, tl.int32)
    tmp2 = tmp0 == tmp1
    tmp5 = 0.0
    tmp6 = tl.where(tmp2, tmp4, tmp5)
    tmp7 = tl.full([1], 2, tl.int32)
    tmp8 = tmp0 == tmp7
    tmp11 = tl.where(tmp8, tmp10, tmp5)
    tmp12 = tmp6 + tmp11
    tmp13 = tl.full([1], 1, tl.int32)
    tmp14 = tmp0 == tmp13
    tmp17 = tl.where(tmp14, tmp16, tmp5)
    tmp18 = tmp12 + tmp17
    tmp19 = tl.full([1], 0, tl.int32)
    tmp20 = tmp0 == tmp19
    tmp23 = tl.where(tmp20, tmp22, tmp5)
    tmp24 = tmp18 + tmp23
    tl.store(out_ptr0 + (x0), tmp24, xmask)
