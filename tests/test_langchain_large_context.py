            "context_relevance_ratio": context_relevance,
            "response_length_words": len(response.split()),
            "response_length_sentences": len(sentences),
            "avg_sentence_length": avg_sentence_length,
            "response_preview": response[:200] + "..." if len(response) > 200 else response
        }
    
    def test_large_context_scenario(
        self, 
        context_manager, 
        llm, 
        test_name: str,
        context_type: str,
        context_content: str,
        test_prompt: str
    ) -> LargeContextTestResult:
        """Test a specific large context scenario"""
        
        try:
            # Measure performance
            performance = self.measure_performance(
                context_manager, llm, test_prompt, context_content
            )
            
            # Build full context for coherence analysis
            full_context = context_manager.build_context(
                base_prompt=test_prompt,
                context_data=context_content
            )
            
            # Generate response for analysis
            response = llm(full_context)
            
            # Analyze coherence
            coherence = self.analyze_coherence_indicators(context_content, response)
            
            return LargeContextTestResult(
                test_name=test_name,
                context_type=context_type,
                context_size_chars=len(context_content),
                estimated_tokens=self.estimate_tokens(context_content),
                success=True,
                performance_metrics=performance,
                error_message=None,
                response_preview=response[:300] + "..." if len(response) > 300 else response,
                coherence_indicators=coherence
            )
            
        except ContextLimitExceededError as e:
            return LargeContextTestResult(
                test_name=test_name,
                context_type=context_type,
                context_size_chars=len(context_content),
                estimated_tokens=self.estimate_tokens(context_content),
                success=False,
                performance_metrics=None,
                error_message=f"Context limit exceeded: {str(e)}",
                response_preview=None,
                coherence_indicators={}
            )
            
        except Exception as e:
            return LargeContextTestResult(
                test_name=test_name,
                context_type=context_type,
                context_size_chars=len(context_content),
                estimated_tokens=self.estimate_tokens(context_content),
                success=False,
                performance_metrics=None,
                error_message=f"Test failed: {str(e)}",
                response_preview=None,
                coherence_indicators={}
            )
    
    def run_screenplay_tests(self, context_manager, llm) -> List[LargeContextTestResult]:
        """Run tests with screenplay content"""
        screenplay_content = self.load_test_sample("screenplay_sample.txt")
        
        test_prompts = [
            "Analyze the main themes and character development in this screenplay.",
            "Summarize the key plot points and dramatic tension in this story.",
            "Identify the science fiction elements and how they serve the narrative.",
            "Evaluate the dialogue quality and character voice consistency.",
            "Describe the story structure and pacing throughout the screenplay."
        ]
        
        results = []
        for i, prompt in enumerate(test_prompts):
            result = self.test_large_context_scenario(
                context_manager=context_manager,
                llm=llm,
                test_name=f"screenplay_test_{i+1}",
                context_type="Feature Film Screenplay",
                context_content=screenplay_content,
                test_prompt=prompt
            )
            results.append(result)
            
        return results
    
    def run_book_chapters_tests(self, context_manager, llm) -> List[LargeContextTestResult]:
        """Run tests with book chapters content"""
        book_content = self.load_test_sample("book_chapters_sample.txt")
        
        test_prompts = [
            "Analyze the world-building and scientific concepts presented in these chapters.",
            "Trace the character arcs and relationships throughout the narrative.",
            "Identify the philosophical themes about human evolution and consciousness.",
            "Evaluate the pacing and narrative structure across multiple chapters.",
            "Summarize the key conflicts and their resolutions in this excerpt."
        ]
        
        results = []
        for i, prompt in enumerate(test_prompts):
            result = self.test_large_context_scenario(
                context_manager=context_manager,
                llm=llm,
                test_name=f"book_chapters_test_{i+1}",
                context_type="Science Fiction Chapters",
                context_content=book_content,
                test_prompt=prompt
            )
            results.append(result)
            
        return results
    
    def run_conversation_tests(self, context_manager, llm) -> List[LargeContextTestResult]:
        """Run tests with long conversation history"""
        conversation_content = self.load_test_sample("conversation_history_sample.txt")
        
        test_prompts = [
            "Summarize the key concerns and findings discussed by the research team.",
            "Identify the main ethical dilemmas raised about AI consciousness.",
            "Trace the evolution of the team's thinking throughout the conversation.",
            "Analyze the different perspectives and areas of disagreement.",
            "Evaluate the proposed solutions and safety measures discussed."
        ]
        
        results = []
        for i, prompt in enumerate(test_prompts):
            result = self.test_large_context_scenario(
                context_manager=context_manager,
                llm=llm,
                test_name=f"conversation_test_{i+1}",
                context_type="Extended Technical Discussion",
                context_content=conversation_content,
                test_prompt=prompt
            )
            results.append(result)
            
        return results
    
    def run_comprehensive_test_suite(
        self, 
        model_path: str,
        context_sizes: List[int] = [32768, 131072, 1000000]
    ) -> Dict[str, List[LargeContextTestResult]]:
        """Run comprehensive test suite across different context sizes"""
        
        all_results = {}
        
        for context_size in context_sizes:
            print(f"\n{'='*60}")
            print(f"Testing with {context_size:,} token context window")
            print(f"{'='*60}")
            
            try:
                # Create appropriate context system
                if context_size <= 32768:
                    context_manager, llm = create_32k_system(model_path)
                    size_label = "32K"
                elif context_size <= 131072:
                    context_manager, llm = create_128k_system(model_path)  
                    size_label = "128K"
                else:
                    context_manager, llm = create_1m_system(model_path)
                    size_label = "1M"
                
                # Run all test categories
                screenplay_results = self.run_screenplay_tests(context_manager, llm)
                book_results = self.run_book_chapters_tests(context_manager, llm)
                conversation_results = self.run_conversation_tests(context_manager, llm)
                
                all_results[f"{size_label}_context"] = (
                    screenplay_results + book_results + conversation_results
                )
                
                # Print summary for this context size
                self.print_context_size_summary(size_label, all_results[f"{size_label}_context"])
                
            except Exception as e:
                print(f"Error testing {context_size:,} context: {str(e)}")
                all_results[f"{context_size}_context_ERROR"] = str(e)
        
        return all_results
    
    def print_context_size_summary(self, size_label: str, results: List[LargeContextTestResult]):
        """Print summary for a specific context size"""
        successful_tests = [r for r in results if r.success]
        failed_tests = [r for r in results if not r.success]
        
        print(f"\n{size_label} Context Results:")
        print(f"  Successful tests: {len(successful_tests)}/{len(results)}")
        
        if successful_tests:
            avg_tps = statistics.mean([r.performance_metrics.tokens_per_second for r in successful_tests])
            avg_memory = statistics.mean([r.performance_metrics.memory_usage_mb for r in successful_tests])
            avg_context_tokens = statistics.mean([r.estimated_tokens for r in successful_tests])
            
            print(f"  Average TPS: {avg_tps:.2f}")
            print(f"  Average Memory Usage: {avg_memory:.2f} MB")
            print(f"  Average Context Size: {avg_context_tokens:,.0f} tokens")
        
        if failed_tests:
            print(f"  Failed tests: {len(failed_tests)}")
            for test in failed_tests:
                print(f"    - {test.test_name}: {test.error_message}")
    
    def generate_detailed_report(self, results: Dict[str, List[LargeContextTestResult]]) -> str:
        """Generate detailed test report"""
        report_lines = [
            "# Phase 2C: Large Context Testing Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Test Overview",
            "This report covers comprehensive testing of large context scenarios with LangChain integration.",
            "",
            "### Test Scenarios:",
            "- **Feature Film Screenplay**: ~11K characters, ~2.8K tokens",
            "- **Science Fiction Chapters**: ~10.5K characters, ~2.6K tokens", 
            "- **Extended Technical Discussion**: ~17.7K characters, ~4.4K tokens",
            "",
        ]
        
        for context_label, test_results in results.items():
            if isinstance(test_results, str):  # Error case
                report_lines.extend([
                    f"## {context_label.replace('_', ' ').title()}",
                    f"**ERROR**: {test_results}",
                    ""
                ])
                continue
                
            successful_tests = [r for r in test_results if r.success]
            failed_tests = [r for r in test_results if not r.success]
            
            report_lines.extend([
                f"## {context_label.replace('_', ' ').title()}",
                f"- Total Tests: {len(test_results)}",
                f"- Successful: {len(successful_tests)}",
                f"- Failed: {len(failed_tests)}",
                ""
            ])
            
            if successful_tests:
                avg_tps = statistics.mean([r.performance_metrics.tokens_per_second for r in successful_tests])
                avg_processing_time = statistics.mean([r.performance_metrics.total_processing_time for r in successful_tests])
                avg_memory = statistics.mean([r.performance_metrics.memory_usage_mb for r in successful_tests])
                
                report_lines.extend([
                    "### Performance Metrics:",
                    f"- Average Tokens/Second: {avg_tps:.2f}",
                    f"- Average Processing Time: {avg_processing_time:.2f}s",
                    f"- Average Memory Usage: {avg_memory:.2f} MB",
                    ""
                ])
                
                # Individual test details
                report_lines.append("### Individual Test Results:")
                for test in successful_tests:
                    report_lines.extend([
                        f"#### {test.test_name}",
                        f"- Context Type: {test.context_type}",
                        f"- Estimated Tokens: {test.estimated_tokens:,}",
                        f"- TPS: {test.performance_metrics.tokens_per_second:.2f}",
                        f"- Processing Time: {test.performance_metrics.total_processing_time:.2f}s",
                        f"- Response Preview: {test.response_preview}",
                        ""
                    ])
            
            if failed_tests:
                report_lines.append("### Failed Tests:")
                for test in failed_tests:
                    report_lines.extend([
                        f"- **{test.test_name}**: {test.error_message}",
                        f"  - Context Size: {test.estimated_tokens:,} tokens",
                        ""
                    ])
        
        return "\n".join(report_lines)


class TestLargeContextIntegration:
    """Pytest integration for large context testing"""
    
    @classmethod
    def setup_class(cls):
        """Set up test class"""
        cls.test_suite = LargeContextTestSuite()
        
        # Try to find Gemma model
        cls.model_path = cls.find_gemma_model()
        if not cls.model_path:
            pytest.skip("No Gemma model found for testing")
    
    @staticmethod
    def find_gemma_model() -> Optional[str]:
        """Find available Gemma model for testing"""
        # Common model locations
        model_locations = [
            "/home/todd/storybench/models",
            "models",
            "../models"
        ]
        
        for location in model_locations:
            model_dir = Path(location)
            if model_dir.exists():
                # Look for Gemma models
                for model_file in model_dir.rglob("*.gguf"):
                    if "gemma" in model_file.name.lower():
                        return str(model_file)
        
        return None
    
    def test_32k_context_scenarios(self):
        """Test all scenarios with 32K context"""
        context_manager, llm = create_32k_system(self.model_path)
        
        # Test each scenario type
        screenplay_results = self.test_suite.run_screenplay_tests(context_manager, llm)
        book_results = self.test_suite.run_book_chapters_tests(context_manager, llm)
        conversation_results = self.test_suite.run_conversation_tests(context_manager, llm)
        
        all_results = screenplay_results + book_results + conversation_results
        
        # Verify at least some tests succeeded
        successful_tests = [r for r in all_results if r.success]
        assert len(successful_tests) > 0, "No tests succeeded with 32K context"
        
        # Verify performance metrics are reasonable
        for result in successful_tests:
            assert result.performance_metrics.tokens_per_second > 0, f"Invalid TPS for {result.test_name}"
            assert result.performance_metrics.total_processing_time > 0, f"Invalid processing time for {result.test_name}"
    
    def test_context_limit_enforcement(self):
        """Test that context limits are properly enforced"""
        # Create a very small context system for testing limits
        from storybench.unified_context_system import UnifiedContextManager
        from storybench.context_config import ContextConfig
        
        # Create 1K context limit for testing
        config = ContextConfig(max_context_size=1024)
        context_manager = UnifiedContextManager(config)
        
        # Try to use large content that should exceed limits
        large_content = self.test_suite.load_test_sample("screenplay_sample.txt")
        
        with pytest.raises(ContextLimitExceededError):
            context_manager.build_context(
                base_prompt="Analyze this content:",
                context_data=large_content
            )
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks meet minimum requirements"""
        context_manager, llm = create_32k_system(self.model_path)
        
        # Test with medium-sized content
        conversation_content = self.test_suite.load_test_sample("conversation_history_sample.txt")
        
        result = self.test_suite.test_large_context_scenario(
            context_manager=context_manager,
            llm=llm,
            test_name="performance_benchmark",
            context_type="Performance Test",
            context_content=conversation_content[:5000],  # Use subset for faster testing
            test_prompt="Summarize the key points in this discussion."
        )
        
        assert result.success, f"Performance test failed: {result.error_message}"
        
        # Verify minimum performance requirements
        metrics = result.performance_metrics
        assert metrics.tokens_per_second > 0.1, f"TPS too low: {metrics.tokens_per_second}"
        assert metrics.total_processing_time < 300, f"Processing too slow: {metrics.total_processing_time}s"
        assert metrics.memory_usage_mb < 2000, f"Memory usage too high: {metrics.memory_usage_mb}MB"


def main():
    """Main function for running comprehensive tests"""
    test_suite = LargeContextTestSuite()
    
    # Find Gemma model
    model_path = TestLargeContextIntegration.find_gemma_model()
    if not model_path:
        print("Error: No Gemma model found for testing")
        print("Please ensure a Gemma model is available in the models directory")
        return 1
    
    print(f"Using model: {model_path}")
    
    # Run comprehensive test suite
    results = test_suite.run_comprehensive_test_suite(model_path)
    
    # Generate and save report
    report = test_suite.generate_detailed_report(results)
    
    report_path = Path("phase2c_large_context_test_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Print final summary
    print("\n" + "="*60)
    print("PHASE 2C LARGE CONTEXT TESTING COMPLETE")
    print("="*60)
    
    total_tests = 0
    total_successful = 0
    
    for context_label, test_results in results.items():
        if isinstance(test_results, list):
            total_tests += len(test_results)
            total_successful += len([r for r in test_results if r.success])
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {total_successful}")
    print(f"Success Rate: {(total_successful/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
    
    return 0 if total_successful > 0 else 1


if __name__ == "__main__":
    exit(main())
