#!/usr/bin/env python3
"""Check Directus prompt lengths to ensure appropriate token limits"""

import os
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))
from storybench.clients.directus_client import DirectusClient

async def check_prompt_lengths():
    """Check the length of prompts from Directus to inform token settings."""
    print("📏 CHECKING DIRECTUS PROMPT LENGTHS")
    print("-" * 40)
    
    try:
        directus_client = DirectusClient()
        
        # Get latest prompts
        prompt_version = await directus_client.get_latest_published_version()
        if not prompt_version:
            print("❌ No published prompt version found")
            return
            
        prompts = await directus_client.convert_to_storybench_format(prompt_version)
        if not prompts or not prompts.sequences:
            print("❌ Failed to fetch prompts")
            return
        
        print(f"📋 Analyzing prompts from v{prompt_version.version_number}")
        
        total_prompts = 0
        max_length = 0
        min_length = float('inf')
        total_chars = 0
        
        for seq_name, seq_prompts in prompts.sequences.items():
            print(f"\n   📝 Sequence: {seq_name}")
            for i, prompt in enumerate(seq_prompts, 1):
                char_count = len(prompt.text)
                # Rough estimate: 1 token ≈ 4 characters
                token_estimate = char_count // 4
                
                print(f"      Prompt {i}: {char_count} chars (~{token_estimate} tokens)")
                print(f"         \"{prompt.text[:60]}...\"")
                
                total_prompts += 1
                max_length = max(max_length, char_count)
                min_length = min(min_length, char_count)
                total_chars += char_count
        
        avg_length = total_chars / total_prompts
        avg_tokens = avg_length // 4
        max_tokens = max_length // 4
        min_tokens = min_length // 4
        
        print(f"\n📊 PROMPT STATISTICS:")
        print(f"   Total prompts: {total_prompts}")
        print(f"   Average length: {avg_length:.0f} chars (~{avg_tokens:.0f} tokens)")
        print(f"   Longest prompt: {max_length} chars (~{max_tokens:.0f} tokens)")
        print(f"   Shortest prompt: {min_length} chars (~{min_tokens:.0f} tokens)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   Current response limit: 512 tokens")
        if max_tokens > 400:
            print(f"   ⚠️  Longest prompt ({max_tokens} tokens) + response (512) = {max_tokens + 512} tokens")
            print(f"   🔍 Consider context window implications for sequence coherence")
        else:
            print(f"   ✅ Prompts are short enough to leave plenty of room for responses")
            
        return {
            "total_prompts": total_prompts,
            "avg_tokens": avg_tokens,
            "max_tokens": max_tokens,
            "min_tokens": min_tokens
        }
        
    except Exception as e:
        print(f"❌ Error checking prompts: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(check_prompt_lengths())
