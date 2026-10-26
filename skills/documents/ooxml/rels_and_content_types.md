# OOXML notes: relationships and content types

Most "the file opens but the feature is gone" reports come from this layer. A new part that is not registered is invisible to Word, and a mis-registered part can make Word declare the whole package corrupt.

## The two registries

| Part                           | Role                                        | Namespace                                                      |
| ------------------------------ | ------------------------------------------- | -------------------------------------------------------------- |
| `word/_rels/document.xml.rels` | names the parts the main document points at | `http://schemas.openxmlformats.org/package/2006/relationships` |
| `[Content_Types].xml`          | declares the media type of every part       | `http://schemas.openxmlformats.org/package/2006/content-types` |

## Relationship entries

Each `Relationship` element carries three attributes:

- `Id` — the handle used from `document.xml` (`rId7`, `rIdComments1`, …); it only has to be unique inside this `.rels` file
- `Type` — the relationship's semantics, e.g. comments, hyperlink, footer
- `Target` — path relative to the part's own folder

Comments, for instance:

```xml
<Relationship Id="rIdComments1"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
  Target="comments.xml"/>
```

External targets (hyperlinks) additionally need `TargetMode="External"`.

## Content-type entries

`Default` entries map an extension; `Override` entries map one specific part. New named parts such as `comments.xml` need an override:

```xml
<Override PartName="/word/comments.xml"
  ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
```

`PartName` is absolute from the package root and starts with `/`.

## When a patched file misbehaves

Check these in order — they catch nearly every case:

1. the part actually exists in the ZIP at the path the relationship names;
2. the relationship `Type` matches the feature and the `Target` resolves relative to `word/`;
3. `[Content_Types].xml` has an override (or a matching default) for it;
4. namespace prefixes and the declaration on each edited part are intact — Word rejects files whose prefixes it cannot resolve;
5. no duplicate `Id` in the `.rels` file and no duplicate `PartName` in the content types.
