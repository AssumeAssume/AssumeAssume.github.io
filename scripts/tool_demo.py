"""A small, explicitly illustrative track-management example for the home page."""

from html import escape


def track_demo():
    tracks = [
        ("atac-control", "ATAC-seq · control", "Accessibility"),
        ("atac-treated", "ATAC-seq · treated", "Accessibility"),
        ("h3k27ac-control", "H3K27ac · control", "Histone mark"),
        ("h3k27ac-treated", "H3K27ac · treated", "Histone mark"),
        ("rna-control", "RNA-seq · control", "Transcription"),
        ("rna-treated", "RNA-seq · treated", "Transcription"),
    ]
    rows = []
    for key, name, kind in tracks:
        rows.append(f'''<li class="track-demo__track" data-demo-track data-track-name="{escape(name)}">
          <input type="checkbox" id="demo-track-{key}" data-demo-select>
          <label for="demo-track-{key}"><span class="track-demo__name">{escape(name)}</span><span class="track-demo__kind">{escape(kind)}</span></label>
          <span class="track-demo__grip" aria-hidden="true">⠿</span>
        </li>''')
    return f'''<section class="track-demo" data-track-demo aria-label="Track management illustration">
      <div class="track-demo__heading"><span class="track-demo__eyebrow">Illustrative demo · example tracks</span><span class="track-demo__count" data-demo-count>0 / 6 selected</span></div>
      <p class="track-demo__intro">Select tracks, filter by name, and move them together.</p>
      <label class="track-demo__filter-label" for="track-demo-filter">Filter tracks by name</label>
      <input class="track-demo__filter" id="track-demo-filter" type="search" data-demo-filter placeholder="Try ATAC or treated" autocomplete="off" spellcheck="false">
      <ol class="track-demo__list" data-demo-list>{''.join(rows)}</ol>
      <p class="track-demo__empty" data-demo-empty hidden>No example tracks match this name.</p>
      <div class="track-demo__actions">
        <button type="button" data-demo-up disabled>Move selected up</button>
        <button type="button" data-demo-down disabled>Move selected down</button>
        <button type="button" data-demo-reset>Reset</button>
      </div>
      <p class="track-demo__status" data-demo-status role="status" aria-live="polite" aria-atomic="true">Choose one or more tracks to try the workflow.</p>
      <p class="track-demo__note">A workflow sketch using synthetic examples; this is not IGV or a real dataset.</p>
    </section>'''
