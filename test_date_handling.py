"""
Test improved date handling in the intelligent interface
"""

from simple_intelligent_interface import simple_intelligent

def test_date_queries():
    print('🧪 Testing improved date handling...')
    print('=' * 50)
    
    # Initialize
    simple_intelligent.initialize()
    
    # Test specific date queries
    test_queries = [
        'What was the maximum temperature on 15 January 2010?',
        'What was the maximum temperature on 10 January 2010?', 
        'What was the maximum temperature on 20 January 2010?'
    ]
    
    for query in test_queries:
        print(f'Query: {query}')
        try:
            result = simple_intelligent.query_with_context(query)
            print(f'Answer: {result.get("answer", "No answer")}')
        except Exception as e:
            print(f'Error: {e}')
        print()

if __name__ == "__main__":
    test_date_queries()