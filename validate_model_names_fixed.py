            # Test generation with a simple prompt
            test_prompt = "Respond with just the word 'Hello'"
            
            # Use correct token parameter for the model
            generation_kwargs = {
                "prompt": test_prompt,
                "temperature": 0.3,
            }
            
            if provider == "openai" and (model_name.startswith("o3") or model_name.startswith("o4")):
                generation_kwargs["max_completion_tokens"] = 20
            else:
                generation_kwargs["max_tokens"] = 20
            
            response_result = await test_evaluator.generate_response(**generation_kwargs)
            
            if response_result and "response" in response_result:
                response_text = response_result["response"].strip()
                generation_time = response_result.get("generation_time", 0)
                print(f"   [{i:2d}/12] ✅ {model_key}: Valid (response: '{response_text[:20]}...', {generation_time:.2f}s)")
                model_results[model_key] = (True, f"Valid - responded in {generation_time:.2f}s")
            else:
                print(f"   [{i:2d}/12] ❌ {model_key}: No response generated")
                model_results[model_key] = (False, "No response generated")            # Test generation with a simple prompt  
            test_prompt = "Respond with just the word 'Hello'"
            
            # Use appropriate token parameter for model type
            if provider == "openai" and (model_name.startswith("o3") or model_name.startswith("o4")):
                response_result = await test_evaluator.generate_response(
                    prompt=test_prompt,
                    temperature=0.3,
                    max_completion_tokens=20
                )
            else:
                response_result = await test_evaluator.generate_response(
                    prompt=test_prompt,
                    temperature=0.3,
                    max_tokens=20
                )