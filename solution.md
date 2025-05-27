

## **Truncation Solution: Token-Aware Dynamic Context Window**

The main goal is to utilize the model's available context window as fully and intelligently as possible, ensuring that context truncation, when necessary, is based on the model's actual token limits rather than arbitrary character counts.

### ---

**1\. Accurate Token Estimation**

The current character-to-token approximation (len(text) // 3\) is too crude and contributes to premature truncation.

* **Action**: Implement a more accurate token counting method.  
  * **Preferred**: Utilize the specific tokenizer associated with the LLM being evaluated. Since your system uses llama.cpp, it should be possible to leverage its tokenization capabilities. This might involve exposing a tokenization function or making a call to a utility that can tokenize text according to the loaded model.  
  * **Alternative**: If direct tokenizer access within the run\_end\_to\_end.py script is challenging, use a robust general-purpose tokenizer library (e.g., tiktoken for models with similar tokenization schemes, or another suitable library for the models you employ).

### ---

**2\. Revise Context Assembly Logic**

Modify the build\_context function in run\_end\_to\_end.py to be token-aware.

* **Calculate Available Tokens**: The system already calculates available\_context\_tokens as n\_ctx \- max\_tokens \- buffer (e.g., 15,884 tokens). This value should be the primary guide for context sizing.  
* **Token-Based Truncation Trigger**:  
  * Instead of if len(full\_sequence\_text) \> 5000:, the condition to truncate should be based on whether the token count of full\_sequence\_text plus the token count of current\_prompt\_text (and any separators) exceeds available\_input\_tokens.  
* **Smart Truncation**:  
  * When full\_sequence\_text needs to be truncated, remove tokens from the *beginning* of full\_sequence\_text, thus preserving the most recent conversational history, which is crucial for sequential prompts.  
  * The amount of text to keep should be determined by how many tokens from the history can fit alongside the current prompt within the available\_input\_tokens.  
  * Convert the target token count back to text to form the truncated\_context.  
* **Refined Truncation Indicator**: The "\[...truncated...\]" message is still useful. The existing logic to find a sentence boundary can be applied to the *beginning* of the truncated\_context (after token-based truncation) to make the transition smoother, rather than truncating mid-sentence.

### ---

**Conceptual Revised build\_context Function:**

Python

\# Located in run\_end\_to\_end.py  
\# Needs access to the model's tokenizer and available\_input\_tokens

def build\_context\_revised(full\_sequence\_text: str, current\_prompt\_text: str,   
                          available\_input\_tokens: int, tokenizer: YourTokenizer) \-\> str:  
    """  
    Builds context for the LLM, respecting token limits and prioritizing recent history.

    Args:  
        full\_sequence\_text: The accumulated text of previous responses in the sequence.  
        current\_prompt\_text: The text of the current prompt.  
        available\_input\_tokens: The number of tokens available for the input context.  
        tokenizer: An object with encode() and decode() methods for the current LLM.  
    """  
      
    history\_prompt\_separator \= "\\n\\n---\\n\\n" \# Separator between history and new prompt \[cite: 26, 28\]

    \# Tokenize current prompt and separator to determine their token cost  
    current\_prompt\_tokens \= tokenizer.encode(current\_prompt\_text)  
    separator\_tokens \= tokenizer.encode(history\_prompt\_separator)

    \# Calculate tokens available for the historical text  
    \# A small buffer for the truncation message itself can be included if desired  
    tokens\_for\_history \= available\_input\_tokens \- len(current\_prompt\_tokens) \- len(separator\_tokens)  
      
    \# Ensure tokens\_for\_history is not negative (prompt itself might be too long)  
    if tokens\_for\_history \< 0:  
        tokens\_for\_history \= 0 \# No space for history; prompt might exceed total context

    history\_tokens \= tokenizer.encode(full\_sequence\_text)  
    final\_history\_text \= full\_sequence\_text  
    is\_truncated \= False

    if len(history\_tokens) \> tokens\_for\_history:  
        is\_truncated \= True  
        \# Keep the most recent 'tokens\_for\_history' tokens  
        truncated\_history\_tokens \= history\_tokens\[-tokens\_for\_history:\]  
        final\_history\_text \= tokenizer.decode(truncated\_history\_tokens)  
          
        \# Optional: Refine the start of final\_history\_text to a sentence boundary  
        \# (Adapt logic from\[cite: 26, 27\], apply to the start of final\_history\_text)  
        \# E.g., search for a boundary like '\\n\\n' or '. ' near the beginning.

    \# Construct the final context string  
    if not full\_sequence\_text: \# No prior history  
        return current\_prompt\_text  
      
    if is\_truncated:  
        \# Use the "\[...truncated...\]" message when history was actually cut  
        \# The refined sentence boundary logic would apply to final\_history\_text here.  
        return f"\[...truncated...\]\\n\\n{final\_history\_text}{history\_prompt\_separator}{current\_prompt\_text}"  
    else:  
        \# History fits entirely  
        return f"{final\_history\_text}{history\_prompt\_separator}{current\_prompt\_text}"

### **Implementation Steps:**

1. **Expose/Select Tokenizer**: Make a tokenizer (matching the local LLM) available within the scope where build\_context is called.  
2. **Pass Parameters**: Ensure available\_input\_tokens (derived from model config ) and the tokenizer are passed to the build\_context\_revised function.  
3. **Replace Old Logic**: In run\_end\_to\_end.py, replace the call to the old build\_context with the new build\_context\_revised. The full\_sequence\_text accumulation logic remains the same.  
4. **Test**: Thoroughly test with various response lengths and sequence depths to ensure it behaves as expected and models receive appropriately sized context.

### ---

**Benefits of this Solution:**

* **Maximizes Context**: Uses the model's actual context window capacity effectively.  
* **Improves Coherence Evaluation**: Provides models with the necessary preceding narrative, making coherence scores valid and meaningful.  
* **Reduces Bias**: Minimizes context length and response order biases, allowing for fairer model comparisons.  
* **Maintains Simplicity**: Modifies existing logic rather than requiring a major architectural redesign (e.g., full summarization pipelines or vector databases).  
* **Reliability**: Bases decisions on token counts, which are the ground truth for LLMs, rather than less reliable character heuristics.

This approach directly tackles the identified architectural flaw and aligns the context management with the system's primary evaluation objectives.

