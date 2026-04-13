"""test component functions

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_j2_ctx_set():
    from pykern import pkunit
    from pykern.pkcollections import PKDict
    from rsconf import component

    r = PKDict()
    component._j2_ctx_set_op(
        r, [], {"x": {"y": PKDict(), "z.z2": 3}, "p.q.r": PKDict()}, "pksetdefault"
    )
    pkunit.pkeq(["y", "z"], sorted(r.x.keys()))
    pkunit.pkeq(3, r.x.z.z2)
    pkunit.pkeq(PKDict(), r.p.q.r)
