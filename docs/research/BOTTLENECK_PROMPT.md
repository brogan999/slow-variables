Working directory: the normaltech-predictions corpus (70 posts)

You are cataloguing every SPECIFIC BOTTLENECK, SPEED LIMIT, or BARRIER TO DIFFUSION/ADOPTION of AI that Arvind Narayanan and Sayash Kapoor name in their essays. "Diffusion" for them means the whole chain from AI method -> product/application -> individual adoption -> organizational/legal/structural adaptation. A bottleneck is anything they say slows, caps, or blocks AI capabilities from turning into real-world use or impact (economic, scientific, legal, safety-related).

Read every file assigned to you in FULL with `cat`. Do not skim.

For each distinct bottleneck output a JSON object:
- "name": short label (3-8 words), e.g. "Reliability of agents", "Tacit knowledge not in training data", "Regulation in high-consequence domains", "Human learning curves", "Clinical trials", "Organizational restructuring / collective action"
- "description": 1-2 sentences in your own words explaining the mechanism as THEY describe it
- "stage": which stage it acts at: "method->product", "product->adoption", "individual adoption", "organizational/structural", "regulatory/legal", "physical/external world", "safety speed limit", "market/economic", "other"
- "domain": where they invoke it: "general", "software engineering", "law", "science", "medicine", "safety", "agents", other
- "quote": VERBATIM excerpt (15-80 words) where they name it. Copy exactly.
- "slug": file name without .md
- "date": from the file header

Be exhaustive; a long essay may name 10-25 distinct bottlenecks. Include bottlenecks they cite approvingly from others (e.g., economists) if they adopt them. Do NOT include capability limitations of models unless they frame them as a barrier to adoption/impact (e.g., "reliability" counts; "can't do math" alone does not).

Write the JSON array to the output path given to you via a Bash heredoc, validate with python3 json.load, and reply with only a count per file.
