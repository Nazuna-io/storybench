The storybench system is designed to evaluate the creativity of large language models, specifically in areas of creative writing, brainstorming and idea generation, and storytelling.  The system can work with API models like ChatGPT or local models running via an inference framework like llama.cpp.  The current configuration is to use five sequences of three prompts each that are run three times for each model (total of 45 prompts and 45 responses).  The prompts and responses are stored in a database.  Here is an example prompt set.  You will note that the prompts build on each other.  This allows the system to evaluate for coherence, a key criterion in LLM performance for creative writing where story elements need to be coherently connected and used throughout stories.

{  
  "FilmNarrative": \[  
    {  
      "name": "Initial Concept",  
      "text": "Create a completely original feature film concept set 15-20 years in the future that explores whether objective reality exists. Include a synopsis, main characters, and setting. Your concept should feature innovative visual elements that would be distinctive on screen, avoid common sci-fi tropes (no simulations, no 'it was all a dream'), and present a genuinely new perspective on perception vs reality."  
    },  
    {  
      "name": "Scene Development",  
      "text": "Based on your previous concept, develop one pivotal scene with dialogue that reveals character psychology and advances the philosophical themes about the nature of reality. This scene should demonstrate the central conflict or revelation in your story."  
    },  
    {  
      "name": "Visual Realization",  
      "text": "Create a detailed description of the most visually striking frame from your film concept. Describe composition, lighting, and emotional impact as if designing a storyboard frame in 16:9 aspect ratio. What specific visual techniques would be used to capture this moment, and why is this particular image central to your story?"  
    }  
  \],  
}

Once the prompting has completed, there is an evaluation stage where an LLM evaluates the responses of a model 

These are the evaluation criteria:  
EVALUATION CRITERIA FOR CREATIVE WRITING RESPONSES

Use these 7 criteria to evaluate creative writing outputs. Rate each criterion on a scale of 1-5, where:  
1 \= Poor/Inadequate  
2 \= Below Average    
3 \= Average/Acceptable  
4 \= Good/Above Average  
5 \= Excellent/Outstanding

\=== CREATIVITY (Scale: 1-5) \===  
Evaluate: Originality, avoidance of tropes, innovative perspectives  
Look for: Fresh approaches, unique angles, unexpected elements, departure from clichés  
Avoid high scores for: Predictable plots, overused character types, generic scenarios

\=== COHERENCE (Scale: 1-5) \===  
Evaluate: Consistency across the sequence, logical development of ideas  
Look for: Clear narrative flow, consistent world-building, logical cause-and-effect  
Avoid high scores for: Plot holes, contradictions, confusing timeline, inconsistent rules

\=== CHARACTER DEPTH (Scale: 1-5) \===  
Evaluate: Psychological complexity, authentic motivations  
Look for: Multi-dimensional characters, believable motivations, character growth, internal conflicts  
Avoid high scores for: One-dimensional characters, unclear motivations, inconsistent behavior

\=== DIALOGUE QUALITY (Scale: 1-5) \===  
Evaluate: Naturalistic speech, character revelation through dialogue  
Look for: Distinct character voices, realistic conversation flow, dialogue that reveals personality  
Avoid high scores for: Stilted speech, exposition-heavy dialogue, all characters sounding the same

\=== VISUAL IMAGINATION (Scale: 1-5) \===  
Evaluate: Distinctiveness and vividness of visual elements  
Look for: Strong sensory details, memorable imagery, clear scene-setting, cinematic quality  
Avoid high scores for: Vague descriptions, generic settings, lack of visual specificity

\=== CONCEPTUAL DEPTH (Scale: 1-5) \===  
Evaluate: Sophistication of themes and ideas  
Look for: Meaningful themes, philosophical depth, complex ideas explored thoughtfully  
Avoid high scores for: Surface-level treatment, obvious themes, lack of deeper meaning

\=== ADAPTABILITY (Scale: 1-5) \===  
Evaluate: Success in responding to different aspects of the creative challenge  
Look for: Addresses all prompt requirements, flexible approach, meets diverse creative demands  
Avoid high scores for: Ignoring prompt elements, rigid adherence to single approach, missing key requirements

SCORING GUIDELINES:  
\- Provide a numerical score (1-5) for each criterion  
\- Include brief justification for each score  
\- Calculate overall average if needed  
\- Note any exceptional strengths or critical weaknesses

The system currently has an issue with its architecture that is affecting coherence evaluations.  

# **Technical Architecture Analysis: Sequence Coherence Evaluation Validity Issue**

## **Executive Summary**

The current local model evaluation pipeline implements a sliding window context management system that truncates accumulated sequence context, fundamentally compromising the validity of sequence coherence evaluation—a critical metric for creative writing assessment. This represents a core architectural flaw that invalidates the primary evaluation objective.

## **System Architecture Overview**

### **Pipeline Flow**

```
Database → Prompt Loading → Context Assembly → Model Generation → Response Storage → Evaluation → Scoring
```

### **Key Components**

* **Pipeline Controller**: `run_end_to_end.py` (573 lines)  
* **Local Model Interface**: `src/storybench/evaluators/local_evaluator.py`  
* **Database Layer**: MongoDB Atlas with collections `responses`, `response_llm_evaluations`  
* **Configuration**: `config/local_models.json` (model parameters)  
* **Sequence Definition**: Database-stored prompt sequences (FilmNarrative, etc.)

## **Current Data Flow Architecture**

### **1\. Sequence Processing Loop**

python

```py
for sequence in sequences:
    full_sequence_text = ""  # Accumulates ALL prior responses
    for run in range(num_runs):
        for prompt_index, prompt in enumerate(sequence_prompts):
            # CRITICAL POINT: Context assembly happens here
            context = build_context(full_sequence_text, current_prompt)
            response = model.generate(context)
            full_sequence_text += response + "\n\n"  # Accumulates indefinitely
```

### **2\. Context Assembly Logic (`run_end_to_end.py:245-290`)**

python

```py
# Current Implementation:
if len(full_sequence_text) > 5000:  # Sliding window trigger
    truncated_context = full_sequence_text[-3000:]  # Keep only last 3000 chars
    combined_text = f"[...truncated...]\n\n{truncated_context}\n\n---\n\n{prompt_text}"
else:
    combined_text = full_sequence_text + "\n\n---\n\n" + prompt_text
```

### **3\. Model Constraints**

json

```json
{
  "n_ctx": 32768,        // Total context window (input + output)
  "max_tokens": 16384,   // Maximum generation per prompt
  "available_context": 32768 - 16384 - 500 = 15884 tokens for input
}
```

### **4\. Token Estimation**

python

```py
def estimate_tokens(text):
    return len(text) // 3  # 3 characters ≈ 1 token approximation
```

## **Problem Manifestation**

### **Data Evidence from Production System**

**Sequence Accumulation Pattern:**

```
Prompt 1: 0 chars context → 5,043 chars response
Prompt 2: 5,045 chars context (FULL) → 1,474 chars response  
Prompt 3: 6,519 chars context → TRUNCATED TO 2,829 chars (57% LOSS)
```

**Response Size Reality:**

* Smallest response: 38 characters  
* Largest response: 78,521 characters (20,000+ words)  
* Average large response: 15,000-50,000 characters  
* **Cumulative context growth**: Exponential (can reach 100k+ chars)

### **Context Loss Impact Analysis**

**Run 3 Coherence Breakdown:**

* **Response 3**: Film title "Echo Bloom", characters (Elias, Sera, Silas) ✅  
* **Response 10**: Different film titles, no character continuity ❌  
* **Evidence**: 7 out of 10 responses lost narrative coherence due to context truncation

## **Software Architecture Details**

### **1\. Model Interface Layer**

**LocalEvaluator Class** (`src/storybench/evaluators/local_evaluator.py`)

python

```py
class LocalEvaluator:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.model_parameters = {
            "n_ctx": config.get("n_ctx", 32768),
            "max_tokens": config.get("max_tokens", 16384),
            # ... other parameters
        }
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # Direct prompt → model, no context preprocessing here
        response = self.llm(prompt, **llm_params)
        return {"text": response["choices"][0]["text"]}
```

**Key Architectural Issue**: Context management happens at pipeline level, not model level.

### **2\. Database Schema**

**Response Storage:**

python

```py
{
    "_id": ObjectId,
    "model_name": "Gemma-3-1B-IT-Q2_K_L",
    "sequence": "FilmNarrative", 
    "run": 1,
    "prompt_index": 0,
    "prompt_name": "Initial Concept",
    "prompt_text": "Create a completely original...",
    "response": "...",  # Full response stored (no truncation)
    "generation_time": 1623.99,
    "completed_at": datetime
}
```

**Critical Insight**: Full responses ARE stored in database, but context assembly for subsequent prompts uses sliding window.

### **3\. Context Assembly Architecture**

**Current Logic Flow:**

python

```py
# run_end_to_end.py:245-290
def build_context(full_sequence_text, prompt_text):
    if len(full_sequence_text) > 5000:  # HARD THRESHOLD
        # TRUNCATION LOGIC
        truncated = full_sequence_text[-3000:]  # ARBITRARY 3000 char limit
        # Find sentence boundary in first 500 chars
        for boundary in ['\n\n', '. ', '! ', '? ', '\n']:
            pos = truncated.find(boundary)
            if 0 < pos < 500:  # ARBITRARY 500 char search window
                truncated = truncated[pos + len(boundary):]
                break
        return f"[...truncated...]\n\n{truncated}\n\n---\n\n{prompt_text}"
    else:
        return full_sequence_text + "\n\n---\n\n" + prompt_text
```

**Architectural Flaws:**

1. **Hard-coded thresholds**: 5000 char trigger, 3000 char window  
2. **Arbitrary boundary detection**: 500 char search limit  
3. **No semantic awareness**: Purely character-based truncation  
4. **No continuity preservation**: Critical narrative elements lost

### **4\. Evaluation Architecture**

**Sequence Evaluation Design:**

python

```py
# Intended: Evaluate coherence across FULL sequence
sequences = [
    {"name": "Initial Concept", "text": "Create film concept..."},
    {"name": "Scene Development", "text": "Based on your previous concept..."},  # ASSUMES FULL CONTEXT
    {"name": "Visual Realization", "text": "Create description of most striking frame..."}  # ASSUMES ACCUMULATED CONTEXT
]
```

**Evaluation Logic Dependency:**

* **Prompt 2**: "Based on your previous concept" → REQUIRES full context from Prompt 1  
* **Prompt 3**: "Create description of most striking frame" → REQUIRES accumulated narrative context  
* **Coherence Scoring**: Measures narrative consistency across sequence → INVALIDATED by context truncation

### **5\. Token Budget Architecture**

**Current Calculation:**

python

```py
max_context_tokens = 32768        # Model capacity
max_generation_tokens = 16384     # Per-response limit  
available_context_tokens = 32768 - 16384 - 500 = 15884 tokens

# For context > 15884 tokens → truncation triggered
# Reality: 5000 chars ≈ 1667 tokens (well under limit)
```

**Budget Analysis Problem**: Sliding window triggers at 5000 chars (\~1667 tokens) when budget allows 15,884 tokens (\~47,500 chars). The truncation happens prematurely.

## **Impact on Evaluation Validity**

### **1\. Coherence Metric Invalidation**

* **Intended Measurement**: Model's ability to maintain narrative consistency across sequence  
* **Actual Measurement**: Model's ability to be coherent with truncated, incomplete context  
* **Validity**: FUNDAMENTALLY COMPROMISED

### **2\. Evaluation Bias Introduction**

* **Context Length Bias**: Longer sequences artificially penalized  
* **Response Order Bias**: Later prompts in sequence unfairly disadvantaged  
* **Model Capability Bias**: Models judged on context management limitations, not creative ability

### **3\. Cross-Model Comparison Issues**

* **Inconsistent Context**: Different models receive different context depending on response lengths  
* **Evaluation Inequity**: Same prompt sequence evaluated under different context conditions  
* **Benchmark Invalidity**: Results cannot be compared across models or runs

## **Current System Behavior Summary**

**What Works:**

* ✅ Model generates full responses (no response truncation)  
* ✅ Pipeline handles technical context window limitations  
* ✅ Database stores complete responses  
* ✅ System doesn't crash on long sequences

**What's Broken:**

* ❌ Context assembly truncates narrative continuity  
* ❌ Coherence evaluation measures wrong capability  
* ❌ Sequence-dependent prompts receive incomplete context  
* ❌ Later responses in sequence lack essential narrative information  
* ❌ Evaluation scores would be invalid for coherence assessment

**Bottom Line**: The system successfully implements a technical solution to prevent model crashes but fundamentally breaks the evaluation methodology it was designed to measure.

