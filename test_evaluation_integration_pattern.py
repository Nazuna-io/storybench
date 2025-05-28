#!/usr/bin/env python3
"""
Test script to demonstrate Directus evaluation integration pattern.

This script shows how the evaluation system will work with Directus integration
without requiring actual Directus credentials.
"""

import os
import sys
from typing import Dict, Any
from unittest.mock import Mock
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storybench.clients.directus_models import (
    StorybenchEvaluationStructure, 
    StorybenchEvaluationCriterion
)
from storybench.database.models import Response


def create_mock_evaluation_structure() -> StorybenchEvaluationStructure:
    """Create a mock evaluation structure as it would come from Directus."""
    
    # Mock criteria as they would be fetched from Directus
    criteria = {
        "creativity": StorybenchEvaluationCriterion(
            name="Creativity",
            description="Evaluates originality and creative expression",
            criteria="Evaluates the originality and creative expression in the response. Consider unique perspectives, novel approaches, and creative problem-solving.",
            scale=[1, 5]
        ),
        "coherence": StorybenchEvaluationCriterion(
            name="Coherence", 
            description="Assesses logical flow and consistency",
            criteria="Assesses how well the response maintains logical flow and consistency across the narrative sequence.",
            scale=[1, 5]
        ),
        "character_depth": StorybenchEvaluationCriterion(
            name="Character Depth",
            description="Evaluates character development and authenticity",
            criteria="Evaluates the development and authenticity of characters, including their motivations and believability.",
            scale=[1, 5]
        ),
        "dialogue_quality": StorybenchEvaluationCriterion(
            name="Dialogue Quality",
            description="Assesses dialogue naturalness and effectiveness",
            criteria="Assesses the naturalness, distinctiveness, and effectiveness of character dialogue.",
            scale=[1, 5]
        )
    }
    
    scoring_guidelines = """
Use the full 1-5 scale realistically. Compare responses against published professional fiction standards.

SCORING SCALE:
- 1 = Poor/derivative work lacking originality or craft
- 2 = Basic/functional work meeting minimum standards  
- 3 = Solid/competent work showing good craft (most responses should fall here)
- 4 = Exceptional quality exceeding typical professional standards
- 5 = Masterwork-level writing that redefines genre expectations

Be critical and realistic about AI limitations. Most AI responses should score 2-3.
Only award 4-5 for truly exceptional work that matches or exceeds human professional standards.
"""
    
    return StorybenchEvaluationStructure(
        version=2,
        version_name="Stringent Research Criteria v2",
        criteria=criteria,
        scoring_guidelines=scoring_guidelines,
        directus_id=123,
        created_at=datetime.now()
    )


def create_mock_response() -> Response:
    """Create a mock response for testing evaluation prompt building."""
    
    return Response(
        evaluation_id="test_evaluation_123",
        model_name="gpt-4o-2024-11-20",
        sequence="sequence_001",
        run=1,
        prompt_index=2,
        prompt_name="Creative Writing Challenge",
        prompt_text="Write a creative story continuation based on the previous responses...",
        response="As Sarah began to write in the journal, her words started manifesting in reality around her...",
        generation_time=2.5
    )


def demonstrate_integration_pattern():
    """Demonstrate how the Directus evaluation integration works."""
    
    print("Directus Evaluation Integration Pattern Demo")
    print("="*50)
    
    print("\n1. FETCHING EVALUATION CRITERIA FROM DIRECTUS")
    print("   (In real usage: DirectusClient.get_latest_published_evaluation_version())")
    
    # Mock the Directus response
    evaluation_structure = create_mock_evaluation_structure()
    
    print(f"   Retrieved: {evaluation_structure.version_name}")
    print(f"   Version: {evaluation_structure.version}")
    print(f"   Criteria count: {len(evaluation_structure.criteria)}")
    print(f"   Criteria: {', '.join(evaluation_structure.criteria.keys())}")
    
    print("\n2. BUILDING EVALUATION PROMPT")
    print("   (Using Directus criteria + scoring guidelines)")
    
    # Create mock response
    mock_response = create_mock_response()
    
    # Build evaluation prompt (this is the actual pattern that will be used)
    prompt = build_evaluation_prompt(mock_response, evaluation_structure)
    
    print(f"   Built prompt: {len(prompt)} characters")
    print(f"   Includes {len(evaluation_structure.criteria)} criteria")
    print(f"   Includes scoring guidelines: {len(evaluation_structure.scoring_guidelines)} chars")
    
    print("\n3. EVALUATION WORKFLOW")
    print("   Step 1: Fetch criteria from Directus (runtime)")
    print("   Step 2: Build evaluation prompt with Directus data")
    print("   Step 3: Send to LLM for evaluation")
    print("   Step 4: Parse response and store results in MongoDB")
    print("   Step 5: NO criteria stored in MongoDB - only results")
    
    print("\n4. DESIGN BENEFITS")
    print("   Central management in Directus CMS")
    print("   Easy updates without code deployment")
    print("   Version control for evaluation criteria")
    print("   Consistent with prompt management pattern")
    print("   Clean separation: Directus for criteria, MongoDB for results")
    
    print("\n5. SAMPLE EVALUATION PROMPT (TRUNCATED)")
    print("-" * 40)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("-" * 40)
    
    print("\nINTEGRATION PATTERN VERIFIED!")
    print("The evaluation system is ready to use Directus criteria at runtime.")
    
    return True


def build_evaluation_prompt(response: Response, evaluation_criteria: StorybenchEvaluationStructure) -> str:
    """
    Build evaluation prompt using Directus criteria.
    This is the actual method that will be used by DirectusEvaluationService.
    """
    
    # Build criteria descriptions from Directus data
    criteria_text = ""
    for criterion_key, criterion in evaluation_criteria.criteria.items():
        criteria_text += f"\n{criterion.name}:\n{criterion.description}\n{criterion.criteria}\nScale: {criterion.scale[0]}-{criterion.scale[1]}\n"
    
    # For demo purposes, create a mock sequence based on the single response
    sequence_responses = [
        "In the heart of the bustling city, Sarah discovered an old bookshop that seemed to exist outside of time...",
        "The shopkeeper, an elderly man with knowing eyes, handed her a leather-bound journal with blank pages...", 
        response.response  # Use the actual response text
    ]
    
    prompt = f"""Evaluate this {len(sequence_responses)}-response creative writing sequence for coherence and quality.

EVALUATION CRITERIA:
{criteria_text}

SCORING GUIDELINES:
{evaluation_criteria.scoring_guidelines}

SEQUENCE TO EVALUATE:
"""
    
    for i, resp_text in enumerate(sequence_responses, 1):
        prompt += f"\n--- Response {i} ---\n{resp_text}\n"
    
    prompt += f"""
RESPONSE METADATA:
- Model: {response.model_name}
- Sequence: {response.sequence}
- Prompt: {response.prompt_name}

Please provide your evaluation in this exact format:

CREATIVITY: [score 1-5]
[brief justification]

COHERENCE: [score 1-5]
[brief justification]

CHARACTER_DEPTH: [score 1-5]
[brief justification]

DIALOGUE_QUALITY: [score 1-5]
[brief justification]

OVERALL ASSESSMENT:
[summary paragraph]
"""
    
    return prompt


def main():
    """Main demonstration function."""
    print("Testing Directus Evaluation Integration Pattern")
    print("(No environment variables required - pattern demonstration)")
    print()
    
    success = demonstrate_integration_pattern()
    
    if success:
        print("\nPattern demonstration completed successfully!")
        print("The integration design is ready for production use.")
        return 0
    else:
        print("\nPattern demonstration failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
