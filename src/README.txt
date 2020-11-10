README

Finn Morrison
Guanglin Zhu

The search approach uses a basic A* implementation. The heuristic is based on looking at how many items are currently
in the inventory. If we already have a tool that is needed, we don't need to make another one. If we have enough of a
material to make whatever needs the most of that material (eg. the furnace needs 8 cobble), then we do not need to get
any more of that item. These values, both for the tools and the materials, are overriden if the goal specifies a required
value greater than the default heuristic.