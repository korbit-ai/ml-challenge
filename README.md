## Korbit Machine Learning Engineer Challenge

The objective of this challenge is to implement a PR reviewer tool utilizing a Large Language Model (LLM) of your choice,
in order to detect potential issues and bugs within pull requests from a repository.

**Make sure to first click the "Use Template" button, on this repository, or click this [link](https://github.com/new?owner=korbit-ai&template_name=ml-challenge&template_owner=korbit-ai).**

## Task

Your task is to improve the PR reviewing system developed in the template code ([ML-engineer-challenge.ipynb](ML-engineer-challenge.ipynb)) using on a Large Language Model (LLM).

### Detailed Tasks:

The challenge focuses on three critical areas requiring innovation and enhancement:

1. **Split Files into Chunks Improvement:**

   - **Current Approach**: The system currently hard-chunks the repository's code files into smaller text blocks to manage context size for LLM analysis, potentially interrupting logical code segments.
   - **Challenge Objective**: Devise a more intelligent method of dividing code into chunks or an entirely new approach to storing and managing code snippets; one that respects logical or functional boundaries within code, ensuring that related code is evaluated together without compromising efficiency.

2. **Retriever Query Generator System Enhancement:**

   - **Current Approach**: The existing system uses straightforward diffs of files to generate queries for retrieving relevant documents from the vector database.
   - **Challenge Objective**: Rethink the logic and strategy behind query formulation for document retrieval. Your goal is to improve the relevance and precision of the retrieved documents, potentially by incorporating additional contextual information from the PR, understanding changes' semantics, or employing advanced query generation techniques.

3. **Revamp the LLM Review Prompt:**
   - **Current Approach**: Reviews are conducted on a per-file basis, with prompts formulated to guide the LLM in inspecting individual files separately.
   - **Challenge Objective**: Explore alternatives to the current one-file-at-a-time review methodology. Consider strategies that could enable a more holistic review of entire PRs, or group related changes more intelligently. Evaluate the feasibility and potential benefits of using an LLM agent system that might review the comprehensive diff in one interaction or through a more sophisticated multi-step conversation with the LLM. Your goal is to make the review process more efficient, thorough, and contextually aware.

**You may choose to work on just one or any number of the above points.**

## Repositories

You will need to detect issues on the following PR of the Langchain repository:

- [Pull Request #13999](https://github.com/langchain-ai/langchain/pull/13999).

The final assesment will be made on the quality of the issues generated on this PR.

We also selected some more PR if you want to diversify your testing:

- [Pull Request #17694](https://github.com/langchain-ai/langchain/pull/17694) - A very large PR (implement firework into langchain)
- [Pull Request #17136](https://github.com/langchain-ai/langchain/pull/17136) - A medium-sized PR (fix a bug in mistralAI embeddings)
- [Pull Request #16596](https://github.com/langchain-ai/langchain/pull/16596) - A small PR (may not find many issues, context-dependent)

## Getting Started

### Use template

To begin this task, create a new private repository using the template button on this repository into your personal Github.

### Setup Python environment

Create the Python Env using conda or your preferred package manager tooling system to get started.

```sh
conda env update -f environment.yml -n korbit-ml-challenge
conda activate korbit-ml-challenge
```

### Make sure to have the right env

You will need to update the `.env` file with the right values.

```sh
cp .env.example .env
```

If you want to generate a `GITHUB_TOKEN` you can follow this [Github tutorial](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

### Begin working on the [Notebook](ML-engineer-challenge.ipynb) in your private repository.

## Expectations:

- **Creativity & Innovation**: We are looking for creative solutions that push the boundaries of the current implementation. Your approach should be novel yet pragmatic, capable of improving the efficiency and effectiveness of the PR review process.
- **Evaluation**: Each proposed enhancement should be accompanied by a rationale explaining why this improvement is beneficial, along with any potential drawbacks or considerations. For example, does retrieving additional context from the code base improve the overall PR review process? We encourage candidates to include any experiments, metrics, or tests that support their proposals - it's very important to consider the output of your code as the most critical piece of this challenge, not simply the code itself.

## Submission Guidelines:

1. As you work, push to your github repository your enhanced notebook with comments and documentation illustrating your thought process and decisions
2. When you have completed your challenge, invite `@korbit-services` as a collaborator in your repository so that we can review your work before the follow-on working session

This challenge is not only about improving upon existing functionalities but also about showcasing your ability to innovate and think critically about complex engineering problems. Good luck, and we look forward to reviewing your enhancements to our PR reviewer LLM system!

