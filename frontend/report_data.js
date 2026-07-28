// Demo findings database for checkmymanuscript mockup report
window.demoFindings = {
  deskReject: [
    {
      location: "Keywords",
      type: "Desk-reject risk",
      flagged: "No keywords were provided in the document.",
      suggested: "Keywords: Transformer architecture; attention mechanism; neural machine translation; sequence transduction; deep learning; parallelization",
      reasoning: "No keywords were provided in the document. Based on the title 'Attention Is All You Need' and the abstract, the paper introduces the 'Transformer' architecture, which relies solely on 'attention mechanisms' and dispenses with recurrence and convolutions for 'sequence transduction' tasks like 'neural machine translation'. It highlights improved 'parallelization' and reduced training time, which are key contributions in 'deep learning'."
    },
    {
      location: "Authors",
      type: "Desk-reject risk",
      flagged: "Ashish Vaswani",
      suggested: null,
      reasoning: "No corresponding author was found. Please specify a corresponding author."
    },
    {
      location: "Results > English Constituency Parsing",
      type: "Desk-reject risk",
      flagged: "The Transformer generalizes well to English constituency parsing (Results are on Section 23 of WSJ)",
      suggested: "Fig. 1: The Transformer generalizes well to English constituency parsing. Results are shown in Section 23 of the WSJ dataset.",
      reasoning: "The table 'tab:parsing-results' must be cited in the text. Additionally, clarify 'WSJ' as a dataset and add a figure number and description to the caption."
    }
  ],
  titlePage: [
    {
      location: "Keywords",
      type: "Desk-reject risk",
      flagged: "No keywords were provided in the document.",
      suggested: "Keywords: Transformer architecture; attention mechanism; neural machine translation; sequence transduction; deep learning; parallelization",
      reasoning: "No keywords were provided in the document. Based on the title 'Attention Is All You Need' and the abstract, the paper introduces the 'Transformer' architecture."
    },
    {
      location: "Authors",
      type: "Desk-reject risk",
      flagged: "Ashish Vaswani",
      suggested: null,
      reasoning: "No corresponding author was found. Please specify a corresponding author."
    },
    {
      location: "Authors",
      type: "Reviewer flag",
      flagged: "illia.polosukhin@gmail.com",
      suggested: null,
      reasoning: "A personal email address (@gmail.com) is used. It is recommended to use an institutional email address for academic publications to ensure professional correspondence."
    },
    {
      location: "Authors",
      type: "Reviewer flag",
      flagged: "University of Toronto",
      suggested: null,
      reasoning: "The institutional affiliation for Aidan N. Gomez is incomplete. Please add the department, city/state/province, and country."
    },
    {
      location: "Authors",
      type: "Reviewer flag",
      flagged: "Google Research",
      suggested: null,
      reasoning: "The institutional affiliation for several authors is incomplete. Please add the city/state/province and country."
    },
    {
      location: "Authors",
      type: "Reviewer flag",
      flagged: "Google Brain",
      suggested: null,
      reasoning: "The institutional affiliation 'Google Brain' is incomplete for multiple authors. Please add the city, state/province, and country."
    }
  ],
  acronyms: [
    {
      location: "Conclusion",
      type: "Reviewer flag",
      flagged: "In this work, we presented the Transformer, the first sequence transduction model based entirely on attention, replacing the recurrent layers most commonly used in encoder-decoder architectures with multi-headed self-attention.",
      suggested: null,
      reasoning: "The acronym 'Transformer' is defined multiple times. Remove this redundant definition to ensure consistent terminology."
    },
    {
      location: "Background",
      type: "Polish",
      flagged: "The goal of reducing sequential computation also forms the foundation of the Extended Neural GPU, ByteNet and ConvS2S.",
      suggested: "The goal of reducing sequential computation also forms the foundation of the Extended Neural GPU, ByteNet and Convolutional Sequence to Sequence.",
      reasoning: "The acronym 'ConvS2S' is undefined and used only 2 times. Write out the full term 'Convolutional Sequence to Sequence' at each occurrence instead."
    },
    {
      location: "Background",
      type: "Polish",
      flagged: "linearly for ConvS2S and logarithmically for ByteNet.",
      suggested: "linearly for Convolutional Sequence to Sequence and logarithmically for ByteNet.",
      reasoning: "The acronym 'ConvS2S' is undefined and used only 2 times. Write out the full term 'Convolutional Sequence to Sequence' at each occurrence instead."
    },
    {
      location: "Position-wise Feed-Forward Networks",
      type: "Polish",
      flagged: "This consists of two linear transformations with a ReLU activation in between.",
      suggested: "This consists of two linear transformations with a Rectified Linear Unit activation in between.",
      reasoning: "The acronym 'ReLU' is undefined and used only 1 times. Write out the full term 'Rectified Linear Unit' at each occurrence instead."
    },
    {
      location: "Optimizer",
      type: "Polish",
      flagged: "We used the Adam optimizer~\\citep{kingma2014adam} with $\\beta_1=0.9$, $\\beta_2=0.98$ and $\\epsilon=10^{-9}$.",
      suggested: "We used the Adaptive moment estimation optimizer~\\citep{kingma2014adam} with $\\beta_1=0.9$, $\\beta_2=0.98$ and $\\epsilon=10^{-9}$.",
      reasoning: "The acronym 'Adam' is undefined and used only 1 times. Write out the full term 'Adaptive moment estimation' at each occurrence instead."
    }
  ],
  structure: [
    {
      location: "Background",
      type: "Reviewer flag",
      flagged: "Background",
      suggested: null,
      reasoning: "The 'Background' section appears before the 'Introduction'. Typically, the Introduction should set the stage and provide context."
    },
    {
      location: "Model Architecture",
      type: "Reviewer flag",
      flagged: "Model Architecture",
      suggested: null,
      reasoning: "The 'Model Architecture' section details the model's components. However, there's a separate top-level section titled 'Why Self-Attention'. The content should be integrated."
    },
    {
      location: "Training",
      type: "Reviewer flag",
      flagged: "Training",
      suggested: null,
      reasoning: "The 'Training' section is placed after 'Why Self-Attention'. Consider reordering to place 'Model Architecture' and 'Training' sections together."
    },
    {
      location: "Attention Visualizations",
      type: "Reviewer flag",
      flagged: "Attention Visualizations",
      suggested: null,
      reasoning: "The 'Attention Visualizations' section is currently a top-level section with no content and appears after the 'Conclusion'."
    }
  ],
  figures: [
    {
      location: "Results > English Constituency Parsing",
      type: "Desk-reject risk",
      flagged: "The Transformer generalizes well to English constituency parsing (Results are on Section 23 of WSJ)",
      suggested: "Fig. 1: The Transformer generalizes well to English constituency parsing. Results are shown in Section 23 of the WSJ dataset.",
      reasoning: "The table 'tab:parsing-results' must be cited in the text. Additionally, clarify 'WSJ' as a dataset."
    },
    {
      location: "Attention Visualizations",
      type: "Reviewer flag",
      flagged: "Many of the attention heads exhibit behaviour that seems related to the structure of the sentence.",
      suggested: "Fig. 1: Examples of attention heads exhibiting sentence structure-related behavior.",
      reasoning: "Added a figure number (Fig. 1) and specified that the examples are from a figure."
    },
    {
      location: "Attention Visualizations",
      type: "Reviewer flag",
      flagged: "Two attention heads, also in layer 5 of 6, apparently involved in anaphora resolution.",
      suggested: "Two attention heads, also in layer 5 of 6, apparently involved in anaphora resolution (n=X).",
      reasoning: "Added missing essential information: sample size (n=X) for statistical data."
    },
    {
      location: "Model Architecture",
      type: "Reviewer flag",
      flagged: "The Transformer - model architecture.",
      suggested: "Fig. 1: The Transformer : model architecture.",
      reasoning: "The figure 'fig:model-arch' needs to be cited in the text."
    }
  ],
  language: [
    {
      location: "Encoder and Decoder Stacks",
      type: "Reviewer flag",
      flagged: "fact that",
      suggested: "the fact that",
      reasoning: "Missing article 'the' before 'fact'."
    },
    {
      location: "Why Self-Attention",
      type: "Reviewer flag",
      flagged: "syntactic and semantic structure of the sentences.",
      suggested: "syntactic and semantic structures of the sentences.",
      reasoning: "Changed 'structure' to 'structures' to agree with the plural subjects."
    },
    {
      location: "Conclusion",
      type: "Reviewer flag",
      flagged: "Making generation less sequential is another research goals of ours.",
      suggested: "Making generation less sequential is another of our research goals.",
      reasoning: "Corrected subject-verb agreement."
    }
  ],
  funding: [
    {
      location: "Funding Statement",
      type: "Reviewer flag",
      flagged: "No funding statement was found.",
      suggested: null,
      reasoning: "A funding statement briefly acknowledges the financial support behind a research project."
    }
  ],
  title: [
    {
      location: "Title",
      type: "Reviewer flag",
      flagged: "Attention Is All You Need",
      suggested: "The Transformer: Attention Is All You Need",
      reasoning: "The title should be more descriptive. Consider adding 'Transformer' to clearly identify the model architecture."
    }
  ],
  abstract: [
    {
      location: "Abstract",
      type: "Reviewer flag",
      flagged: "On the WMT 2014 English-to-French translation task...",
      suggested: "On the Workshop on Machine Translation (WMT) 2014 English-to-French...",
      reasoning: "Define the acronym WMT upon first use."
    }
  ]
};
