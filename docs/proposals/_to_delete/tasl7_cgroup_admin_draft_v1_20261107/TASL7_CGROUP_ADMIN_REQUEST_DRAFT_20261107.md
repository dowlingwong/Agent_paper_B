# TASL-7 cgroup-v2 delegation — administrator request draft

AI-assisted (Codex). **DRAFT FOR AUTHOR REVIEW — NOT SENT.** No administrator has been contacted for this request. The observations below are point-in-time, independently reviewed read-only results; the proposed inquiry does not authorize B1 or any site changes.

> Subject: Site-supported delegated cgroup-v2 scope for UID 1011 on TASL-7
>
> Hello,
>
> Could you advise how UID 1011 (`dowling`) can start a research runner in a dedicated, user-owned cgroup-v2 scope on TASL-7, without affecting existing services or other users' work?
>
> A read-only SSH inspection on 7 November 2026 at 13:08 UTC showed that the shell belonged to `/user.slice/user-1011.slice/session-61325.scope`. Its session scope was root-owned and not writable in a separate inspection. The common ancestor `/sys/fs/cgroup/user.slice/user-1011.slice/cgroup.procs` was root-owned, mode 644, and not writable by UID 1011. The sibling `user@1011.service/cgroup.procs` was owned by UID 1011 and reported writable. A `user.delegate` attribute check returned `NOT CHECKABLE`; we did not infer whether the subtree is delegated to this project. These permissions and the session name may change.
>
> The current reviewed runner derives its parent solely from its own unified `/proc/self/cgroup` membership, requires that directory to be owned by its UID, and needs to create an exclusive child and worker leaf with working `cgroup.procs`, `cgroup.freeze`, and `cgroup.events`. It does not accept an arbitrary cgroup parent path. The observed common-ancestor permissions suggest that direct unprivileged migration from the inspected SSH scope into the sibling user-manager subtree may fail; **no migration or freezer test was attempted**. The writable sibling alone does not establish that it is available for this work.
>
> Is there a site-supported way to launch the runner initially inside an appropriately delegated UID-1011-owned scope, or can an administrator arrange one? Please specify the supported launch procedure, delegation and freezer permissions, any relevant site limits, and how to keep the scope isolated from existing services. The project must not preempt other work and currently requires retained test cgroups and files: it must not delete or clean up its test artifacts. Please also advise whether retention is acceptable under the site's cgroup policy and whether automatic service or scope cleanup would occur.
>
> We have not changed any cgroup or system service. We will independently review the proposed procedure and run a separate, test-owned capability check before considering the research run.
>
> Thank you.

**Evidence:** [read-only result](../reports/TASL7_CGROUP_DELEGATION_BOUNDARY_RESULT_20261107.md), [independent review](../reviews/TASL7_CGROUP_DELEGATION_BOUNDARY_RESULT_REVIEW_20261107.md). The administrator's response and any launch procedure require separate review; this draft is not permission to send a message or start a probe. No complete B1 checkout, test suite, author gate, or handover is accepted by this request.
