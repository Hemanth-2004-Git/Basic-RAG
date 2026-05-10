"""
Generate sample PDFs for the RAG knowledge base.
Run this once to create the knowledge documents.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

os.makedirs("knowledge_base", exist_ok=True)
styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title', parent=styles['Title'], spaceAfter=20)
heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], spaceAfter=10)
body_style = ParagraphStyle('Body', parent=styles['Normal'], spaceAfter=8, leading=16)


def make_pdf(filename, title, sections):
    doc = SimpleDocTemplate(
        f"knowledge_base/{filename}",
        pagesize=letter,
        rightMargin=inch, leftMargin=inch,
        topMargin=inch, bottomMargin=inch
    )
    story = [Paragraph(title, title_style), Spacer(1, 0.2 * inch)]
    for heading, paras in sections:
        story.append(Paragraph(heading, heading_style))
        for p in paras:
            story.append(Paragraph(p, body_style))
        story.append(Spacer(1, 0.15 * inch))
    doc.build(story)
    print(f"  Created: knowledge_base/{filename}")


# ── PDF 1: Artificial Intelligence Overview ─────────────────────────────────
make_pdf("ai_overview.pdf", "Artificial Intelligence: A Comprehensive Overview", [
    ("What is Artificial Intelligence?", [
        "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines "
        "that are programmed to think and learn. The field covers a wide range of techniques "
        "including machine learning, deep learning, natural language processing, computer vision, "
        "and robotics.",
        "AI systems can perform tasks that traditionally required human intelligence: recognising "
        "speech, translating languages, diagnosing diseases, playing complex games, and driving "
        "vehicles autonomously.",
    ]),
    ("History of AI", [
        "The term 'Artificial Intelligence' was coined by John McCarthy in 1956 during the "
        "Dartmouth Conference. Early AI research focused on symbolic reasoning and problem-solving.",
        "The 1980s saw the rise of expert systems. The 1990s brought machine learning methods. "
        "The 2010s witnessed a deep-learning revolution fuelled by large datasets and powerful GPUs. "
        "Today, foundation models and generative AI are reshaping every industry.",
    ]),
    ("Machine Learning", [
        "Machine Learning (ML) is a subset of AI that enables systems to learn from data without "
        "being explicitly programmed. Key paradigms are supervised learning (labelled data), "
        "unsupervised learning (pattern discovery), and reinforcement learning (reward signals).",
        "Popular ML algorithms include linear regression, decision trees, random forests, support "
        "vector machines, k-nearest neighbours, and gradient boosting.",
    ]),
    ("Deep Learning", [
        "Deep Learning uses multi-layered artificial neural networks inspired by the human brain. "
        "Convolutional Neural Networks (CNNs) excel at image recognition; Recurrent Neural Networks "
        "(RNNs) and Transformers handle sequential data like text and audio.",
        "GPT, BERT, and Vision Transformers are landmark deep-learning architectures that have "
        "achieved state-of-the-art performance across many benchmarks.",
    ]),
    ("Applications of AI", [
        "Healthcare: AI assists in medical imaging, drug discovery, and personalised treatment plans.",
        "Finance: fraud detection, algorithmic trading, credit scoring, and robo-advisors.",
        "Transportation: self-driving cars, traffic optimisation, and predictive maintenance.",
        "Education: adaptive learning platforms, automated grading, and intelligent tutoring.",
        "Entertainment: content recommendation (Netflix, Spotify), game AI, and generative art.",
    ]),
    ("Ethical Considerations", [
        "AI raises important ethical questions around bias, fairness, privacy, accountability, and "
        "the displacement of jobs. Responsible AI development requires transparent models, diverse "
        "training data, and robust governance frameworks.",
        "Organisations such as the EU AI Act and IEEE are working on regulations and guidelines to "
        "ensure AI is developed and deployed safely and ethically.",
    ]),
])

# ── PDF 2: Python Programming Guide ─────────────────────────────────────────
make_pdf("python_guide.pdf", "Python Programming: From Basics to Advanced", [
    ("Introduction to Python", [
        "Python is a high-level, interpreted, general-purpose programming language created by "
        "Guido van Rossum and released in 1991. Its design philosophy emphasises code readability "
        "and simplicity, making it one of the most popular languages worldwide.",
        "Python supports multiple paradigms: procedural, object-oriented, and functional programming. "
        "It runs on Windows, macOS, Linux, and can even run in the browser via WebAssembly.",
    ]),
    ("Core Data Types", [
        "Python's built-in types include int, float, complex, bool, str, bytes, list, tuple, "
        "set, frozenset, and dict. Dynamic typing means variables do not need explicit type "
        "declarations, though type hints (PEP 484) are encouraged for large codebases.",
        "Lists are mutable ordered sequences; tuples are immutable. Dictionaries map unique keys "
        "to values and maintain insertion order since Python 3.7.",
    ]),
    ("Functions and Modules", [
        "Functions are defined with the 'def' keyword. Python supports default arguments, "
        "keyword arguments, *args, **kwargs, and lambda expressions for anonymous functions.",
        "Modules group related code into files; packages group modules into directories. "
        "The Python Package Index (PyPI) hosts over 500,000 packages installable via pip.",
    ]),
    ("Object-Oriented Programming", [
        "Classes are defined with the 'class' keyword. Python supports single and multiple "
        "inheritance, mixins, abstract base classes (abc module), dataclasses, and metaclasses.",
        "Dunder (double-underscore) methods like __init__, __str__, __repr__, __len__, and "
        "__iter__ let you integrate custom objects with Python's built-in operations.",
    ]),
    ("Popular Libraries", [
        "Data Science: NumPy (arrays), Pandas (dataframes), Matplotlib & Seaborn (visualisation).",
        "Machine Learning: scikit-learn, TensorFlow, PyTorch, Keras, XGBoost.",
        "Web Development: Django (batteries-included), Flask (micro-framework), FastAPI (async).",
        "Automation: Selenium, Playwright, Beautiful Soup, Scrapy.",
        "DevOps: Ansible, Fabric, Paramiko.",
    ]),
    ("Best Practices", [
        "Follow PEP 8 style guidelines. Use virtual environments (venv or conda). Write unit tests "
        "with pytest or unittest. Document code with docstrings. Use type hints for clarity.",
        "Favour composition over inheritance, keep functions small and focused, and rely on "
        "Python's built-in data structures before reaching for external libraries.",
    ]),
])

# ── PDF 3: Machine Learning Fundamentals ────────────────────────────────────
make_pdf("ml_fundamentals.pdf", "Machine Learning Fundamentals", [
    ("The ML Pipeline", [
        "A typical ML project follows these steps: (1) define the problem, (2) collect and explore "
        "data (EDA), (3) preprocess and feature-engineer, (4) select and train a model, "
        "(5) evaluate, (6) tune hyperparameters, (7) deploy, (8) monitor and retrain.",
    ]),
    ("Supervised Learning", [
        "In supervised learning, each training example is paired with a label. Regression predicts "
        "continuous values (house prices); classification predicts discrete classes (spam vs ham).",
        "Key algorithms: Linear Regression, Logistic Regression, Decision Trees, Random Forest, "
        "Gradient Boosted Trees (XGBoost, LightGBM), Support Vector Machines, Neural Networks.",
    ]),
    ("Unsupervised Learning", [
        "Unsupervised learning discovers hidden structure in unlabelled data. Clustering groups "
        "similar points (K-Means, DBSCAN, Hierarchical Clustering). Dimensionality reduction "
        "compresses features (PCA, t-SNE, UMAP, Autoencoders).",
        "Association rule learning finds co-occurrence patterns in transactional data (Apriori, FP-Growth).",
    ]),
    ("Model Evaluation", [
        "Regression metrics: MAE, MSE, RMSE, R² score.",
        "Classification metrics: accuracy, precision, recall, F1-score, ROC-AUC, confusion matrix.",
        "Cross-validation (k-fold) provides a robust estimate of generalisation performance and "
        "reduces variance from a single train/test split.",
    ]),
    ("Overfitting and Regularisation", [
        "Overfitting occurs when a model memorises training data but performs poorly on unseen data. "
        "Underfitting happens when a model is too simple to capture the underlying pattern.",
        "Regularisation techniques: L1 (Lasso), L2 (Ridge), Elastic Net, dropout (neural nets), "
        "early stopping, data augmentation, and increasing training data size.",
    ]),
    ("Feature Engineering", [
        "Feature engineering transforms raw data into informative inputs. Techniques include "
        "one-hot encoding (categorical variables), scaling (StandardScaler, MinMaxScaler), "
        "polynomial features, interaction terms, and target encoding.",
        "Feature selection methods: filter methods (correlation, chi-squared), wrapper methods "
        "(RFE), embedded methods (LASSO coefficients, tree feature importance).",
    ]),
])

# ── PDF 4: RAG and LLMs ──────────────────────────────────────────────────────
make_pdf("rag_and_llms.pdf", "Retrieval-Augmented Generation (RAG) and Large Language Models", [
    ("What are Large Language Models?", [
        "Large Language Models (LLMs) are neural networks trained on massive text corpora to "
        "predict the next token in a sequence. Models like GPT-4, Claude, Gemini, and Llama "
        "have billions of parameters and can generate coherent, contextually relevant text.",
        "LLMs exhibit emergent capabilities: reasoning, code generation, translation, summarisation, "
        "and question answering — all from a single pre-trained model fine-tuned on instructions.",
    ]),
    ("Transformer Architecture", [
        "The Transformer (Vaswani et al., 2017) introduced self-attention, allowing every token to "
        "attend to every other token in the sequence. Positional encodings preserve word order.",
        "Key components: multi-head self-attention, feed-forward layers, layer normalisation, "
        "residual connections, and (in decoders) cross-attention over encoder outputs.",
    ]),
    ("What is RAG?", [
        "Retrieval-Augmented Generation (RAG) combines a retrieval system with a generative LLM. "
        "Instead of relying solely on the model's parametric knowledge, RAG fetches relevant "
        "documents from an external knowledge base and includes them in the prompt context.",
        "RAG addresses LLM hallucination, knowledge cutoff, and the inability to cite sources — "
        "making it ideal for enterprise knowledge bases, customer support, and research assistants.",
    ]),
    ("RAG Pipeline", [
        "Indexing phase: Documents are split into chunks, embedded with a sentence encoder, and "
        "stored in a vector store (FAISS, Pinecone, Weaviate, Chroma).",
        "Query phase: The user query is embedded, a similarity search retrieves the top-k chunks, "
        "and they are injected into the LLM prompt as context before generation.",
    ]),
    ("Vector Databases", [
        "Vector databases store high-dimensional embeddings and support approximate nearest "
        "neighbour (ANN) search. FAISS (Meta) is an open-source library for efficient similarity "
        "search; Pinecone and Weaviate are managed cloud services.",
        "Common distance metrics: cosine similarity (angle between vectors), L2 (Euclidean), "
        "and dot product. For normalised embeddings cosine and dot product are equivalent.",
    ]),
    ("Best Practices", [
        "Chunk size matters: too small loses context; too large dilutes relevance. 256-512 tokens "
        "with 10-15% overlap is a good starting point.",
        "Re-ranking: after retrieval, a cross-encoder re-ranks candidates for higher precision.",
        "Hybrid search: combine dense (vector) retrieval with sparse (BM25/keyword) retrieval.",
        "Evaluate with RAGAS metrics: faithfulness, answer relevancy, context precision & recall.",
    ]),
])

print("\nAll sample PDFs created successfully in the 'knowledge_base/' folder!")
