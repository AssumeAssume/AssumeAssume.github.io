"""Accessible, conceptual illustrations for the research notebook homepage."""

from html import escape


def _control(theme, label, feature, caption, selected=False):
    active = ' class="is-active"' if selected else ''
    return (
        f'<button type="button"{active} data-locus-focus="{feature}" '
        f'data-locus-caption="{escape(caption, quote=True)}" '
        f'aria-pressed="{str(selected).lower()}" '
        f'aria-controls="locus-{theme}-figure locus-{theme}-caption">'
        f'{escape(label)}</button>'
    )


def _svg(theme, title, description, drawing):
    return f'''<svg id="locus-{theme}-figure" class="locus-figure"
      viewBox="0 0 560 270" role="group"
      aria-labelledby="locus-{theme}-title locus-{theme}-description">
      <title id="locus-{theme}-title">{escape(title)}</title>
      <desc id="locus-{theme}-description">{escape(description)}</desc>
      <path class="genome-track" d="M 36 176 H 524" fill="none" />
      <path class="genome-track" d="M 36 181 H 524" fill="none" />
      {drawing}
      <text class="locus-axis-label" x="36" y="257">Genomic context</text>
    </svg>'''


def _panel(theme, drawing, controls, caption, note, source, source_label, selected=False):
    hidden = '' if selected else ' hidden'
    return f'''<div id="lens-{theme}" class="lens-panel" role="tabpanel"
      aria-labelledby="tab-{theme}"{hidden}>
      {drawing}
      <p class="locus-note">{escape(note)}</p>
      <div class="locus-controls" role="group" aria-label="Explore {source_label}">
        {''.join(controls)}
      </div>
      <p id="locus-{theme}-caption" class="locus-caption" role="status"
        aria-live="polite" aria-atomic="true">{escape(caption)}</p>
      <a class="locus-source" href="{source}">{escape(source_label)} <span aria-hidden="true">↗</span></a>
    </div>'''


def research_locus():
    """Return a complete component; assets/editorial.js wires its interactions."""
    line1_caption = (
        'LINE-1 transcription promotes long-range chromatin contacts and distal gene activation.'
    )
    line1 = _svg(
        'line1',
        'LINE-1 and a distant target gene',
        'A conceptual genome track connects an active LINE-1 element with a distant target '
        'gene through a long-range chromatin contact. The diagram has no genomic coordinates.',
        '''<path class="locus-arc is-emphasized" data-locus-feature="line1 contact gene"
          role="button" tabindex="0" data-locus-focus="contact" aria-pressed="false"
          aria-label="Explore the long-range contact"
          d="M 122 160 C 166 40, 374 40, 420 160" fill="none" />
        <text class="locus-diagram-label" x="280" y="42" text-anchor="middle">Long-range contact</text>
        <g class="locus-element is-emphasized" data-locus-feature="line1"
          role="button" tabindex="0" data-locus-focus="line1" aria-pressed="true"
          aria-label="Explore LINE-1">
          <rect x="80" y="159" width="84" height="35" rx="2" />
          <path d="M 106 148 H 145 M 138 141 L 146 148 L 138 155" fill="none" />
        </g>
        <g class="locus-element" data-locus-feature="gene"
          role="button" tabindex="0" data-locus-focus="gene" aria-pressed="false"
          aria-label="Explore the target gene">
          <path d="M 366 159 H 454 L 470 176.5 L 454 194 H 366 Z" />
        </g>
        <text class="locus-diagram-label" x="122" y="221" text-anchor="middle">LINE-1</text>
        <text class="locus-diagram-label" x="419" y="221" text-anchor="middle">Target gene</text>'''
    )
    line1_controls = [
        _control('line1', 'LINE-1', 'line1', line1_caption, True),
        _control('line1', 'Long-range contact', 'contact',
                 'Chromatin contacts link LINE-1 transcription with regulation of distant genes.'),
        _control('line1', 'Target gene', 'gene',
                 'Distal gene activation connects LINE-1 transcription to broader regulatory programs.'),
    ]

    ankrd11_caption = (
        'ANKRD11 condensates restrain hypertranscribed regions and safeguard transcriptional '
        'control during development.'
    )
    ankrd11 = _svg(
        'ankrd11',
        'ANKRD11 and transcriptional restraint',
        'A conceptual genome track places an ANKRD11 condensate around a hypertranscribed '
        'gene to illustrate transcriptional restraint. This is a conceptual illustration, '
        'not a measurement of condensate structure or size.',
        '''<g role="button" tabindex="0" data-locus-focus="condensate" aria-pressed="true"
          aria-label="Explore the ANKRD11 condensate">
        <ellipse class="locus-boundary is-emphasized" data-locus-feature="condensate"
          cx="380" cy="138" rx="124" ry="80" pointer-events="all" />
        <text class="locus-diagram-label" x="380" y="42" text-anchor="middle">ANKRD11 condensate</text>
        <g class="locus-element is-emphasized" data-locus-feature="condensate">
          <circle cx="304" cy="118" r="9" />
          <circle cx="342" cy="92" r="9" />
          <circle cx="401" cy="86" r="9" />
          <circle cx="455" cy="111" r="9" />
        </g>
        </g>
        <g class="locus-element" data-locus-feature="gene"
          role="button" tabindex="0" data-locus-focus="gene" aria-pressed="false"
          aria-label="Explore the hypertranscribed gene">
          <path d="M 326 159 H 416 L 432 176.5 L 416 194 H 326 Z" />
        </g>
        <g class="locus-arc" data-locus-feature="transcription" fill="none"
          role="button" tabindex="0" data-locus-focus="transcription" aria-pressed="false"
          aria-label="Explore transcriptional restraint">
          <path d="M 348 143 C 351 128, 359 151, 365 136 S 378 150, 384 137 S 397 148, 403 136" />
          <path d="M 384 118 V 127 M 374 118 H 394" />
        </g>
        <text class="locus-diagram-label" x="101" y="138" text-anchor="middle">Chromatin</text>
        <text class="locus-diagram-label" x="380" y="235" text-anchor="middle">Hypertranscribed gene</text>'''
    )
    ankrd11_controls = [
        _control('ankrd11', 'ANKRD11', 'condensate', ankrd11_caption, True),
        _control('ankrd11', 'Hypertranscribed gene', 'gene',
                 'Highly transcribed developmental loci reveal where transcriptional control '
                 'needs to be safeguarded.'),
        _control('ankrd11', 'Transcriptional restraint', 'transcription',
                 'Our study examines how ANKRD11 restricts hypertranscription during development.'),
    ]

    ai_caption = (
        'I aim to understand how distributed cis-regulatory information shapes gene expression '
        'across cell states, using interpretable AI.'
    )
    ai = _svg(
        'ai',
        'Distributed regulatory information and interpretable AI',
        'A conceptual genome track contains multiple enhancers, a promoter and a gene. '
        'Connections to an interpretable model illustrate the research direction: relating '
        'distributed regulatory information to gene expression. No model prediction is displayed.',
        '''<g class="locus-arc" data-locus-feature="enhancers model" fill="none">
          <path d="M 92 159 C 95 101, 179 105, 237 70" />
          <path d="M 184 159 C 184 115, 249 108, 280 70" />
          <path d="M 276 159 C 276 111, 312 109, 323 70" />
        </g>
        <path class="locus-arc" data-locus-feature="locus model"
          d="M 331 69 C 396 85, 421 112, 421 159" fill="none" />
        <g class="locus-element" data-locus-feature="model"
          role="button" tabindex="0" data-locus-focus="model" aria-pressed="false"
          aria-label="Explore interpretable AI">
          <rect x="198" y="26" width="165" height="44" rx="2" />
          <text class="locus-diagram-label" x="280.5" y="53" text-anchor="middle">Interpretable AI</text>
        </g>
        <g class="locus-element is-emphasized" data-locus-feature="enhancers"
          role="button" tabindex="0" data-locus-focus="enhancers" aria-pressed="true"
          aria-label="Explore enhancers">
          <rect x="73" y="159" width="38" height="35" rx="2" />
          <rect x="165" y="159" width="38" height="35" rx="2" />
          <rect x="257" y="159" width="38" height="35" rx="2" />
        </g>
        <g class="locus-element" data-locus-feature="locus"
          role="button" tabindex="0" data-locus-focus="locus" aria-pressed="false"
          aria-label="Explore the gene locus">
          <rect x="351" y="159" width="15" height="35" rx="2" />
          <path d="M 382 159 H 459 L 475 176.5 L 459 194 H 382 Z" />
        </g>
        <text class="locus-diagram-label" x="184" y="221" text-anchor="middle">Enhancers</text>
        <text class="locus-diagram-label" x="407" y="221" text-anchor="middle">Promoter + gene</text>'''
    )
    ai_controls = [
        _control('ai', 'Enhancers', 'enhancers', ai_caption, True),
        _control('ai', 'Gene locus', 'locus',
                 'I study how promoters, enhancers, sequence and chromatin work together '
                 'across different cell states.'),
        _control('ai', 'Interpretation', 'model',
                 'The goal is to connect gene-expression predictions with interpretable '
                 'regulatory mechanisms.'),
    ]

    return f'''<div class="research-locus">
      <div class="locus-topline"><span>At the locus</span><span>Conceptual illustration</span></div>
      <div class="lens-tabs" role="tablist" aria-label="Research themes">
        <button id="tab-line1" type="button" role="tab" data-lens="line1"
          aria-selected="true" aria-controls="lens-line1" tabindex="0">LINE-1</button>
        <button id="tab-ankrd11" type="button" role="tab" data-lens="ankrd11"
          aria-selected="false" aria-controls="lens-ankrd11" tabindex="-1">ANKRD11</button>
        <button id="tab-ai" type="button" role="tab" data-lens="ai"
          aria-selected="false" aria-controls="lens-ai" tabindex="-1">Regulatory AI</button>
      </div>
      {_panel('line1', line1, line1_controls, line1_caption,
               'Distance is only part of the story.', '#pub-line1', 'Nature Genetics · 2024', True)}
      {_panel('ankrd11', ankrd11, ankrd11_controls, ankrd11_caption,
               'Transcription also needs restraint.', '#pub-ankrd11', 'Cell · 2026')}
      {_panel('ai', ai, ai_controls, ai_caption,
               'Prediction is useful. Explanation is the goal.', '#research', 'Current research direction')}
    </div>'''
