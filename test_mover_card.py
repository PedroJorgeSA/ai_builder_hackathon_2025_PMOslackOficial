"""
Teste Local da Funcionalidade de Mover Cards
Execute: python test_mover_card.py
"""

import sys
import os

# Adicionar o path da API
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

def test_intent_classifier():
    """Testa o classificador de intenções"""
    from utils.intent_classifier import classify_with_openai
    
    print("=" * 80)
    print("🧪 TESTE DO INTENT CLASSIFIER")
    print("=" * 80)
    print()
    
    # Casos de teste
    test_cases = [
        "mover card Login para Concluído",
        "mover card Fazer apresentação para A fazer",
        "mover card testar deploy para A fazer",
        'mover card "Login" para Concluído',
        "mover Login para Concluído",
        "mover o card Login para a lista Concluído",
        "mudar Login pra Em Progresso",
        "transferir card API para Revisão",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"📝 Teste {i}: '{text}'")
        print('─' * 80)
        
        result = classify_with_openai(text)
        
        print(f"\n✅ Intent: {result.get('intent')}")
        print(f"✅ Confiança: {result.get('confidence')}")
        print(f"✅ Parâmetros:")
        params = result.get('params', {})
        print(f"   • Card: '{params.get('card_name')}'")
        print(f"   • Lista: '{params.get('target_list')}'")
        
        # Verificar se extraiu corretamente
        if params.get('card_name') and params.get('target_list'):
            print(f"\n✅ SUCESSO - Extraiu ambos os parâmetros!")
        else:
            print(f"\n❌ FALHOU - Parâmetros faltando!")
            if not params.get('card_name'):
                print(f"   ❌ Falta: card_name")
            if not params.get('target_list'):
                print(f"   ❌ Falta: target_list")


def test_move_card_handler():
    """Testa o handler de mover cards (requer credenciais do Trello)"""
    print("\n\n")
    print("=" * 80)
    print("🧪 TESTE DO HANDLER DE MOVER CARDS")
    print("=" * 80)
    print()
    
    # Verificar se tem credenciais
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('TRELLO_API_KEY')
    token = os.getenv('TRELLO_TOKEN')
    board_id = os.getenv('TRELLO_BOARD_ID')
    
    if not all([api_key, token, board_id]):
        print("⚠️ Credenciais do Trello não configuradas no .env")
        print("   Configure TRELLO_API_KEY, TRELLO_TOKEN e TRELLO_BOARD_ID")
        print("   para testar o handler completo.")
        return
    
    print("✅ Credenciais encontradas!")
    print(f"   • Board ID: {board_id}")
    print()
    
    # Listar cards disponíveis
    import urllib.request
    import json
    
    print("📋 Buscando cards disponíveis...")
    cards_url = f'https://api.trello.com/1/boards/{board_id}/cards?key={api_key}&token={token}'
    req = urllib.request.Request(cards_url)
    response = urllib.request.urlopen(req)
    cards = json.loads(response.read())
    
    print(f"\n✅ Total de cards no board: {len(cards)}")
    if cards:
        print("\n📝 Primeiros cards:")
        for i, card in enumerate(cards[:5], 1):
            print(f"   {i}. {card['name']}")
    
    # Listar listas disponíveis
    print("\n📋 Buscando listas disponíveis...")
    lists_url = f'https://api.trello.com/1/boards/{board_id}/lists?key={api_key}&token={token}'
    req = urllib.request.Request(lists_url)
    response = urllib.request.urlopen(req)
    lists = json.loads(response.read())
    
    print(f"\n✅ Total de listas no board: {len(lists)}")
    if lists:
        print("\n📝 Listas:")
        for i, lst in enumerate(lists, 1):
            print(f"   {i}. {lst['name']}")
    
    print("\n" + "─" * 80)
    
    # Teste de busca
    if cards and lists:
        print("\n🔍 TESTE DE BUSCA:")
        print()
        
        # Testar busca de card
        test_card_name = "login"
        matching_cards = [c for c in cards if test_card_name.lower() in c['name'].lower()]
        
        print(f"Buscando cards com '{test_card_name}':")
        if matching_cards:
            print(f"✅ Encontrou {len(matching_cards)} card(s):")
            for card in matching_cards:
                print(f"   • {card['name']}")
        else:
            print(f"❌ Nenhum card encontrado")
        
        print()
        
        # Testar busca de lista
        test_list_name = "concluído"
        matching_lists = [l for l in lists if test_list_name.lower() in l['name'].lower()]
        
        print(f"Buscando listas com '{test_list_name}':")
        if matching_lists:
            print(f"✅ Encontrou {len(matching_lists)} lista(s):")
            for lst in matching_lists:
                print(f"   • {lst['name']}")
        else:
            print(f"❌ Nenhuma lista encontrada")


def test_full_flow():
    """Testa o fluxo completo: classifier + handler"""
    print("\n\n")
    print("=" * 80)
    print("🧪 TESTE DO FLUXO COMPLETO")
    print("=" * 80)
    print()
    
    # Verificar credenciais
    from dotenv import load_dotenv
    load_dotenv()
    
    if not all([os.getenv('TRELLO_API_KEY'), os.getenv('TRELLO_TOKEN'), os.getenv('TRELLO_BOARD_ID')]):
        print("⚠️ Configure as credenciais do Trello para testar o fluxo completo")
        return
    
    # Importar handler
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api', 'slack'))
    
    print("Digite um comando de mover card (ou 'sair' para terminar):")
    print("Exemplo: mover card Login para Concluído")
    print()
    
    while True:
        try:
            command = input("👉 Comando: ").strip()
            
            if command.lower() in ['sair', 'exit', 'quit', '']:
                break
            
            print()
            print("─" * 80)
            
            # Classificar intent
            from utils.intent_classifier import classify_with_openai
            result = classify_with_openai(command)
            
            print(f"Intent: {result.get('intent')}")
            params = result.get('params', {})
            print(f"Card: '{params.get('card_name')}'")
            print(f"Lista: '{params.get('target_list')}'")
            
            if result.get('intent') == 'trello_move_card' and params.get('card_name') and params.get('target_list'):
                print("\n✅ Parâmetros extraídos com sucesso!")
                print("\n⚠️ Simulação - não vou mover de verdade neste teste")
                print(f"   Moveria: '{params.get('card_name')}' → '{params.get('target_list')}'")
            else:
                print("\n❌ Falhou em extrair os parâmetros")
            
            print("─" * 80)
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            print()


def main():
    """Função principal"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🧪 TESTE LOCAL - MOVER CARDS                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Menu
    print("Escolha o teste:")
    print("1. Testar apenas o Intent Classifier")
    print("2. Testar Handler (requer credenciais)")
    print("3. Testar Fluxo Completo (interativo)")
    print("4. Executar todos os testes")
    print()
    
    choice = input("👉 Opção (1-4): ").strip()
    
    if choice == '1':
        test_intent_classifier()
    elif choice == '2':
        test_move_card_handler()
    elif choice == '3':
        test_full_flow()
    elif choice == '4':
        test_intent_classifier()
        test_move_card_handler()
        test_full_flow()
    else:
        print("❌ Opção inválida")
    
    print("\n")
    print("=" * 80)
    print("✅ TESTES CONCLUÍDOS!")
    print("=" * 80)
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

