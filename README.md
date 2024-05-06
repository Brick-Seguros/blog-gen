# Blog Post Generator
![alt text](./assets/blog-gen.png)

### Overview
This is a simple tool that generates blog posts from given questions. 

It was built based on a paper called STORM - Synthesis of Topic Outlines through
Retrieval and Multi-perspective Question Asking.

The intuition to generate a blog post from a given topic is:
- We build a outline of the expected result
- We generate 5 others related topics
- We create 3 different experts (LLM Prompts) based on those topics and an external knowledge base. (In this case *Blog das Locadoras* and *Google Search*) 
- We conduct an interview process with each one of those experts. 
- We use those discussions to refine our outline and write each of those sections.
- With the refined outline and the draft of the sections we use Long Context LLMs to write the full article. 

![alt text](./assets/image.png)

### Installation

```
    pip install -r requirements.txt
```

### Execution

```
    python app.py
```

### Web Interface
It was used taipy to create a quick web interface.

```
    cd taipy

    python main.py
```

### Next Steps
Iterate on how to build the best experts.

How to bring the right context about Brick's business.

How to optimize for SEO.

### References

- STORM Paper: https://arxiv.org/pdf/2402.14207

- Langchain implementation: https://github.com/langchain-ai/langgraph/blob/main/examples/storm/storm.ipynb