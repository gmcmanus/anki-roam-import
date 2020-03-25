# Anki Roam Import

Anki add-on to import cloze notes from [Roam](https://roamresearch.com/).

Mark up your cloze deletions in Roam with curly brackets `{like this}`, export
your Roam database to JSON, and then import it into Anki. The addon will create
a cloze note for each Roam block (bullet point) that is marked up with curly
brackets.

## Why?

Roam provides a low-friction way to record, refine, and link your ideas.
Some of the notes you make in Roam are worth remembering using Anki,
and it is nicer to edit them in context in Roam rather than writing them one at a time in Anki.

## Installation

Ensure you have a recent version of [Anki](https://apps.ankiweb.net/) installed
(2.1.16 or newer).

1. Copy this code to your clipboard:
   ```
   1172449017
   ```
2. Open the Anki desktop application.
3. In the Anki main window menu, choose "Tools" then "Add-ons".
4. Click the "Get Add-ons..." button.
5. Paste the code you copied above into the text box, then click the OK button.

## Creating cloze notes in Roam

You should be familiar with how Anki supports
[cloze deletion](https://apps.ankiweb.net/docs/manual.html#cloze-deletion).

To indicate a Roam block (bullet point) should be converted into an Anki cloze
note, put single curly brackets around each cloze deletion `{like this}`.

*Tip*: if you select some text in Roam and then press the `{` key, it will
surround that text in curly brackets. This can be a fast way to mark up cloze
deletions.
 
The add-on will automatically number the clozes when it is imported into Anki.
If you want to create Anki cards with multiple cloze deletions, then you can
number the cloze deletions manually. Indicate the cloze number
`{c1|like this}`. You don't need to indicate cloze numbers in all of the cloze
deletions - the unnumbered cloze deletions will be automatically numbered
differently.

You can indicate cloze hints `{like this|hint}`. You can have both a cloze
cloze number and a hint `{c1|like this|hint}`.

Some examples of how the Roam blocks are converted to Anki notes:

Roam block | Anki note
---------- | -------------
`{Automatic} {cloze} {numbering}.` | `{{c1::Automatic}} {{c2::cloze}} {{c3::numbering}}.`
`{c2\|Manual} {c1\|cloze} {c2\|numbering}.` | `{{c2::Automatic}} {{c1::cloze}} {{c2::numbering}}.`
`{c2\|Mix} of {automatic} and {c2\|manual} {c1\|numbering}.` | `{{c2::Mix}} of {{c3::automatic}} and {{c2::manual}} {{c1::numbering}}.`
`{Cloze\|with hint} and {c3\|another\|with another hint}.` | `{{c1::Cloze::with hint}} and {{c3::another::with another hint}}.`

The Roam cloze deletion syntax has some differences from the Anki syntax:

* It uses `{single curly brackets}` because `{{double curly brackets}}` have
  another meaning in Roam (e.g. `{{[TODO]}}` is used to create a to-do item
  checkbox).
* It uses a vertical pipe `|` because double colons `::` have another meaning in
  Roam (to create
  [attributes](https://roamresearch.com/#/v8/help/page/LJOc7nRiO)).
* Cloze numbers are optional to make the notes easier to write.

## Exporting and importing

To export from Roam:

1. Click on the ellipsis button (...) in the top right menu, then choose
   "Export All". (You can also choose "Export" to export just the current page,
   but it's easier to export all each time. Don't worry, the add-on won't import
   [duplicate notes](#duplicate-notes).)
2. Choose JSON as the export format and click the Export All button.
   You will download a ZIP file.
   
To import into Anki:

1. In the Anki main window menu, choose "Tools" then "Import Roam notes...".
2. Choose the ZIP file you downloaded from Roam.
3. Any new notes will be imported and a dialog will show how many were imported
   and how many were ignored.

You can then check which notes were created by looking in the card browser.

### Duplicate notes

Notes that already exist in the deck will not be imported.

In addition, the add-on records every note it imports to a file,
and it won't import the same note twice.
This means that after you import a note into Anki,
you can change that Anki note as you like (e.g. edit it or delete it),
and it the old note won't be imported again.


## Configuration

You can configure the add-on by choosing "Add-ons" from the "Tools" menu,
selecting the add-on and then clicking the "Config" button. The configuration
fields are:

* `model_name` is the name of the model to use for imported notes. Defaults to
  "Cloze".
* `content_field` is the name of the field in which to put the content of the
  note. Defaults to "Text".
* `source_field` is the name of the field in which to put the source of the note.
  Defaults to null, which means the source is not recorded.
* `deck_name` is the name of the deck in which to put the imported cards.
  Defaults to null, which means use the default deck.

## Indicating the source of the note

If you configure the source_field
then the add-on will record the source of each note in that field.

If you put a Roam block (bullet point) that begins with 'Source:' (case insensitive)
near the block of the Roam cloze note, then it will be recorded as the source of
the note. The add-on looks for sources in these locations:
* Immediate children of the note block.
* Parent of the note block, its parents, and so on.


## Areas for improvement

* Currently only a single Roam block is used to create a single Anki note.
* Better conversion of Roam Markdown into Anki HTML e.g. links
