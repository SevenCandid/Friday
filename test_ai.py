from core import ai_layer

print("Testing AI Layer Connection...")

if not ai_layer.is_available():
    print("❌ ERROR: Ollama is not running. Please start the Ollama app.")
    exit()

print("✅ Ollama is running!\n")

# A complex paragraph that needs explaining
sample_text = """
Quantum entanglement is a physical phenomenon that occurs when a group of particles 
are generated, interact, or share spatial proximity in a way such that the quantum state 
of each particle of the group cannot be described independently of the state of the others, 
including when the particles are separated by a large distance.
"""

print("Original Text:")
print(sample_text.strip())
print("-" * 50)

print("\n🤖 Friday's AI Explanation (Running via Llama 3.2):")
print("Thinking...")
explanation = ai_layer.explain(sample_text)

print("\nResult:")
print(explanation)
