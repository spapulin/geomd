# GeoMarkdown Specification

**Spec version:** 0.1.0\
**Last revised:** 2026-09-29\
**Editors:** Sergei Papulin

GeoMarkdown is a Markdown dialect for geodata. It adds two things to plain Markdown:

1. A **metadata comment** that renames headings and adds extra fields when converting to GeoJSON.
2. A **`geometry` fenced block** that holds GeoJSON geometry inline.


## Document Structure

A GeoMarkdown document is a CommonMark document. Headings establish a hierarchy:

- The **top-level heading** (typically `#`) names the collection and becomes `FeatureCollection.title`.
- A **second-level heading** (typically `##`) becomes a `Feature` when one of its direct subsections contains a ` ```geometry ` block.
- The **feature heading** becomes `Feature.title` and goes to `properties` as well.
- Its **direct subsections** (typically `###`) become `properties`.
- If a **direct subsection** contains a ` ```geometry ` block, that subsection becomes `Feature.geometry` instead of a property.

**Example**

````markdown
# Document Title

## Feature A

### Property 1
Content

### Property 2
```geometry
{"type": "Point", "coordinates": [2.1527, 41.4145]}
```

## Feature B

### Property 1
Content

````
*A section without a direct geometry subsection is not a feature.*

## Metadata comment

An HTML comment placed directly under a heading:

```markdown
## Park Güell
<!--
field_mapping:
    - Overview: overview
    - On map: geometry
extra_fields:
    - id: 1
    - author: Adam Smith
-->
```

The heading becomes a GeoJSON `Feature`. Its subsections become properties.

**`field_mapping`** renames a subsection. Left side is the heading text, right side is the GeoJSON key.
  
**`extra_fields`** adds key/value pairs directly to the feature's `properties`.
  
Mapping a heading to `geometry` makes that subsection the feature's geometry instead of a property.

## Geometry block

A fenced block with the language `geometry`:

````markdown
```geometry
{"type": "Point", "coordinates": [2.1527, 41.4145]}
```
````

The body must be a valid GeoJSON geometry.

## Converting from GeoMarkdown to GeoJSON

For each section:
- The heading becomes `Feature.title`.
- Each subsection becomes a property, renamed per `field_mapping`.
- `extra_fields` are merged into `properties`.
- A subsection mapped to `geometry` becomes `Feature.geometry`.

By default, the parser does not write any metadata back into the GeoJSON.

**Notes**

Property values are strings. A parser reads the subsection's content as text; a renderer writes each value back as text. No type inference is performed.

**Example**

Input:
````markdown
# Barcelona Tour

## Park Güell

<!--
field_mapping:
	- Overview: overview
	- Address: address
	- On map: geometry

extra_fields:
	- id: 1
	- author: Adam Smith
-->

### Overview

A colorful park designed by Antoni Gaudí

### Address

Carrer d'Olot, Barcelona, Spain

### On map

```geometry
{"type": "Point", "coordinates": [2.1527, 41.4145]}
```
````
*A `field_mapping` entry mapping a heading to geometry is optional on the forward direction*

Output:
```json
{
  "type": "FeatureCollection",
  "title": "Barcelona Tour",
  "features": [
    {
      "type": "Feature",
      "title": "Park Güell",
      "geometry": {
        "type": "Point",
        "coordinates": [2.1527, 41.4145]
      },
      "properties": {
        "id": "1",
        "author": "Adam Smith",
        "overview": "A colorful park designed by Antoni Gaudí",
        "address": "Carrer d'Olot, Barcelona, Spain",
        "title": "Park Güell"
      }
    }
  ]
}
```

## Converting from GeoJSON to GeoMarkdown

A renderer accepts an optional `_metadata` member on each `Feature`:

```json
{
    "type": "FeatureCollection", 
    "title": "Barcelona Tour", 
    "features": [
        {
            "type": "Feature", 
            "title": "Park Güell", 
            "_metadata": {
                "field_mapping": {
                    "overview": "Overview",
                    "address": "Address",
                    "geometry": "On map"
                },
                "extra_fields": ["id", "author", "title"]
            },
            "geometry": {
              "type": "Point", 
              "coordinates": [2.1527, 41.4145]
            }, 
            "properties": {
                "id": "1", 
                "author": "Adam Smith", 
                "overview": "A colorful park designed by Antoni Gaudí.", 
                "address": "Carrer d'Olot, Barcelona, Spain", 
                "title": "Park Güell"
            }
        }
    ] 
}
```

`field_mapping` is the inverse of the Markdown version: key becomes heading.

`extra_fields` lists names only; values come from `properties`.

If `_metadata` is absent, the renderer uses defaults: every property becomes a subsection with its key as the heading, and no comment is emitted.


**Notes**

- The Markdown-to-GeoJSON direction is lossy for mappings. Keep your `.md` file if you want them back.
- `title` and `_metadata` are foreign members on `Feature`. GeoJSON tools that don't know about them will ignore them.
- `geometry`, `_metadata`, and `title` are reserved names.
