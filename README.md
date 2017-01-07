SCObidoo
========

Add Statecharts to Odoo models.

The Odoo workflow engine is being abandoned by Odoo SA,
and has performance issues.

This is meant as a replacement, based on the Statechart
paradigm.

Roadmap
-------

* handle return values
* can we do without the StatechartMixin abstract class? for now it's
  here because it's easier to add the register_hook, but more importantly
  to add the sc_state; maybe it's possible to have a custom field type
  to hold sc_state and the asociated interpreter state, simimlar to alfodoo's cmisfield
* make statechart.yaml a computed field (possibly bidirectional) so the statechart
  can be created (and extended) with standard Odoo records
* have a Odoo UI to create statechart records
* and many important implementation details TODO's in the code
