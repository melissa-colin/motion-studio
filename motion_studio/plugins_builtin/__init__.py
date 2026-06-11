"""Built-in Motion Studio plugins (corrector + metrics + floor).

These are simple, original *reference* plugins so the editor works out of the
box: :class:`~motion_studio.plugins_builtin.corrector.Corrector` grounds each
frame onto the floor plane,
:class:`~motion_studio.plugins_builtin.metrics.Metrics` reports a few geometric
quality numbers, and :class:`~motion_studio.plugins_builtin.floor.Floor` fits a
generic ground plane to the lowest foot points. They satisfy the
``MotionCorrector`` / ``MotionMetrics`` / ``MotionFloor`` protocols in
``motion_studio.core`` and are meant to be swapped out for your own via
``--corrector`` / ``--metrics`` / ``--floor`` (see ``docs/PLUGINS.md``).
"""
