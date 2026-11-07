# .drawio file format and editing rules

## Anatomy

```xml
<mxfile host="embed.diagrams.net">
  <diagram id="page-1" name="Page-1">
    <mxGraphModel dx="800" dy="600" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- every shape and arrow goes here, parent="1" (or a container's id) -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

- Cells `0` and `1` are required: `0` is the root, `1` the default layer. Never remove or renumber them.
- Each `<diagram>` is a page (tab). Most files have one; see "Splitting across pages" below for when to add more.
- **Grid and page view are off:** write `grid="0"` and `page="0"` on every new `<mxGraphModel>` (the server's editor also defaults both off). They are view settings only: coordinates still snap to 10, and James can switch either back on under View. On an existing diagram, leave whatever he saved.
- **Shape (vertex):** `<mxCell id="…" value="label" style="…" vertex="1" parent="1"><mxGeometry x="…" y="…" width="…" height="…" as="geometry"/></mxCell>`
- **Arrow (edge):** `<mxCell id="…" value="optional label" style="…" edge="1" parent="1" source="<shape id>" target="<shape id>"><mxGeometry relative="1" as="geometry"/></mxCell>`. An edge's `<mxGeometry>` may contain `<Array as="points">` waypoints James added; keep them.
- **Compressed pages:** if `<diagram>` contains a base64 blob instead of `<mxGraphModel>`, it was saved compressed elsewhere (`encodeURIComponent`, then deflate-raw, then base64). The server's editor saves uncompressed. Decode it to edit (`node -e` with `zlib.inflateRawSync` then `decodeURIComponent`), or ask James to open and Save it once through the server page.

## Editing without wrecking James's work

- **Change only what was asked.** Leave the `id`, `style` and `<mxGeometry>` of existing cells exactly as they are. Layout is James's: don't move his shapes to tidy up.
- **Edit in place**, with targeted edits to the cells concerned. Rewrite the whole file only when creating it.
- **New ids:** unique and readable, from the label: `step-validate`, `dec-has-attachment`, `edge-validate-to-route`.
- **Deleting a shape:** also delete every edge whose `source` or `target` is that shape, and any cell whose `parent` is it.
- **Labels:** XML-escape (`&amp;` `&lt;` `&gt;` `&quot;`). With `html=1` in the style, a line break is `&lt;br&gt;`.
- **Placement:** put new shapes in empty space, near what they connect to, continuing the flow's direction. Reserve a clear right-hand column for yellow question and decision notes; stack active notes there and place answered notes below them or consolidate them into an answered-decisions note. Find free space from existing geometries before choosing `x`/`y`.
- **Grid:** snap to 10. Default shape 160×60 (decisions 160×80), 80 px gap along the flow, 60 px between parallel branches. Flow runs top to bottom unless the existing diagram runs left to right.
- **Splitting across pages:** one page should read at a glance. When a page passes about 15 main shapes, or its arrows can't be routed without crossing shapes, split it: page 1 is the overview (one box per stage), and each busy stage gets its own `<diagram>` with a unique `id` and a `name` saying what it shows. Link an overview box to its detail page with `link="data:page/id,<diagram id>"` on the `<mxCell>`, and end the box's label with " →" so James knows it's clickable. Keep the question notes on the page they concern. Splitting an existing diagram is a layout change: propose it to James, don't just do it.
- If your additions came out cramped, tell James that **Arrange > Layout** (vertical flow) tidies the whole diagram in one click; whether to use it is his call.
- After editing, check the file is still well-formed XML: `python3 -c "import sys,xml.dom.minidom as m; m.parse(sys.argv[1])" <file>` (silent means good). Where python is missing, open the diagram through the server page yourself, or ask James to reload; the editor reports malformed XML.

## Avoiding overlap

Overlap is the most common way a generated diagram goes wrong. Plan coordinates before writing, then check them.

- **Shapes never touch.** Keep at least 40 px between any two shapes' boxes (`x`, `y`, `width`, `height`), including notes and lane edges; inside a swimlane, keep 20 px from the lane's walls and below its 30 px title bar.
- **Text fits its shape.** At the default 12 px font, allow about 7 px per character plus 20 px padding per line. If the label won't fit in two or three lines, widen or heighten the shape, or shorten the label. Never let text spill out of a shape.
- **An arrow touches only its two ends.** Before adding an edge, trace its path. If the straight or elbow route would cross another shape, add waypoints (`<Array as="points"><mxPoint x="…" y="…"/></Array>` inside its `<mxGeometry>`) that run it through the empty gap between shapes, or move the new shape so the path is clear. Long arrows crossing lanes go along a free channel at least 20 px from any shape, not through the middle of a lane.
- **Arrows don't share a path.** Two edges into or out of one shape use different sides or points: set `exitX`/`exitY` and `entryX`/`entryY` (0 to 1 across the shape, e.g. `exitX=1;exitY=0.3;` and `exitX=1;exitY=0.7;`). Never draw two edges between the same pair in the same direction; merge their labels instead.
- **Edge labels sit on a clear stretch.** Keep labels to one or two words, and place them where the line crosses empty space, not over a shape, another label or a crossing. Move one along its edge with the geometry's `x` (-1 to 1, 0 is the middle) and off it with `<mxPoint as="offset" x="…" y="…"/>`.
- **Reduce crossings first, route second.** Order shapes so connected ones are neighbours in the flow; most crossings disappear before any waypoint is needed. Prefer one lane per actor over long cross-diagram lines; if a single link would cross the whole page, consider splitting the page instead.
- **Check before handing over.** List every shape's box and every edge's path (its waypoints, or the elbow between its ends) and confirm: no two boxes within 40 px, no edge passing through a box other than its source and target, no label on top of a shape or another label. Fix what fails before telling James it's ready.

## Flowchart vocabulary

Common style strings. Keep shapes uncoloured by default. When colour carries meaning (say, who does a step), use at most three fills and add a small legend note: bot/automated `fillColor=#dae8fc;strokeColor=#6c8ebf;`, human `fillColor=#f8cecc;strokeColor=#b85450;`, external system `fillColor=#d5e8d4;strokeColor=#82b366;`. Yellow is reserved for open-question notes.

| Meaning | Style |
| --- | --- |
| Step / action | `rounded=1;whiteSpace=wrap;html=1;` |
| Decision (yes/no) | `rhombus;whiteSpace=wrap;html=1;` |
| Start / end | `ellipse;whiteSpace=wrap;html=1;` |
| Input / output data | `shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;` |
| Stored data (DB) | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=15;` |
| External system / subprocess | `shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;` |
| Human-in-the-loop | `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;` (40×60) |
| Note / open question | `shape=note;whiteSpace=wrap;html=1;size=14;fillColor=#fff2cc;strokeColor=#d6b656;` |
| Group / lane (container) | `swimlane;whiteSpace=wrap;html=1;startSize=30;` children use `parent="<lane id>"` and coordinates relative to it |
| Arrow | `edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;` |
| Dashed arrow (async / optional) | arrow style + `dashed=1;` |

Label decision branches on the edge (`value="yes"` / `value="no"`).

**Topic map:** the subject as an ellipse (200×80) near the centre of the page, e.g. `x=320 y=480`; branches as steps placed in a ring about 260 px out, each joined to the centre by a plain arrow with `endArrow=none;`. Sub-points sit a further 200 px out from their branch.

## Minimal complete example

Start → step → decision → two ends:

```xml
<mxfile host="embed.diagrams.net">
  <diagram id="page-1" name="Page-1">
    <mxGraphModel grid="0" gridSize="10" guides="1" connect="1" arrows="1" page="0" pageWidth="850" pageHeight="1100">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="start" value="Email arrives" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="320" y="40" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="step-classify" value="Classify request" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="320" y="180" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="dec-urgent" value="Urgent?" style="rhombus;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="320" y="320" width="160" height="80" as="geometry" />
        </mxCell>
        <mxCell id="end-page" value="Page on-call" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="480" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="end-queue" value="Add to queue" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="540" y="480" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="edge-start-classify" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="start" target="step-classify">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge-classify-urgent" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="step-classify" target="dec-urgent">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge-urgent-page" value="yes" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="dec-urgent" target="end-page">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge-urgent-queue" value="no" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="dec-urgent" target="end-queue">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
