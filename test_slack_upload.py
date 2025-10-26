"""
Script para testar upload de imagem no Slack
Verifica token e permissões ANTES de fazer deploy
"""

import os
import io
import json
import urllib.request
import urllib.error

def test_slack_upload():
    """Testa se o token do Slack tem permissão para fazer upload"""
    
    # Ler token do ambiente ou pedir ao usuário
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    
    if not slack_token:
        print("❌ SLACK_BOT_TOKEN não encontrado no ambiente")
        slack_token = input("\n📝 Cole o Bot User OAuth Token do Slack aqui: ").strip()
    
    if not slack_token.startswith('xoxb-'):
        print("⚠️ Token parece inválido (deve começar com 'xoxb-')")
        print(f"   Você digitou: {slack_token[:10]}...")
    
    print(f"\n✅ Token encontrado: {slack_token[:15]}...")
    
    # Testar autenticação
    print("\n🔍 Testando autenticação...")
    try:
        url = 'https://slack.com/api/auth.test'
        headers = {'Authorization': f'Bearer {slack_token}'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        
        if result.get('ok'):
            print(f"✅ Autenticação OK!")
            print(f"   Bot: @{result.get('user', 'unknown')}")
            print(f"   Team: {result.get('team', 'unknown')}")
        else:
            print(f"❌ Erro de autenticação: {result.get('error')}")
            return
    except Exception as e:
        print(f"❌ Erro ao testar autenticação: {e}")
        return
    
    # Pedir ID do canal
    print("\n📝 Preciso do ID do canal para testar upload")
    print("   Como obter:")
    print("   1. Abra o Slack no navegador")
    print("   2. Vá no canal desejado")
    print("   3. Na URL, copie o código após /messages/ (ex: C01234ABCD)")
    
    channel_id = input("\n📢 Cole o ID do canal aqui: ").strip()
    
    # Criar uma imagem de teste simples
    print("\n🎨 Criando imagem de teste...")
    
    try:
        # Tentar usar matplotlib
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, '✅ TESTE DE UPLOAD\nSe você vê isso, funcionou!', 
                ha='center', va='center', fontsize=20, fontweight='bold')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        image_data = buf.read()
        print(f"✅ Imagem criada: {len(image_data)} bytes")
    
    except ImportError:
        print("⚠️ matplotlib não instalado, criando imagem fake...")
        # Criar um PNG mínimo válido (1x1 pixel transparente)
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # Fazer upload
    print(f"\n📤 Fazendo upload para canal {channel_id}...")
    
    boundary = '----TestBoundary123456'
    body_parts = []
    
    # Campo: channels
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(b'Content-Disposition: form-data; name="channels"')
    body_parts.append(b'')
    body_parts.append(channel_id.encode())
    
    # Campo: filename
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(b'Content-Disposition: form-data; name="filename"')
    body_parts.append(b'')
    body_parts.append(b'teste_upload.png')
    
    # Campo: title
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(b'Content-Disposition: form-data; name="title"')
    body_parts.append(b'')
    body_parts.append(b'Teste de Upload')
    
    # Campo: initial_comment
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(b'Content-Disposition: form-data; name="initial_comment"')
    body_parts.append(b'')
    body_parts.append('🧪 Teste de upload de imagem - Se voce ve isso, esta funcionando!'.encode('utf-8'))
    
    # Campo: file
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(b'Content-Disposition: form-data; name="file"; filename="teste_upload.png"')
    body_parts.append(b'Content-Type: image/png')
    body_parts.append(b'')
    body_parts.append(image_data)
    
    # Finalizar
    body_parts.append(f'--{boundary}--'.encode())
    body_parts.append(b'')
    
    body_bytes = b'\r\n'.join(body_parts)
    
    print(f"   Tamanho do corpo: {len(body_bytes)} bytes")
    
    try:
        url = 'https://slack.com/api/files.upload'
        headers = {
            'Authorization': f'Bearer {slack_token}',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        
        req = urllib.request.Request(url, data=body_bytes, headers=headers)
        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read())
        
        print(f"\n📋 Resposta do Slack:")
        print(json.dumps(result, indent=2))
        
        if result.get('ok'):
            print(f"\n✅ SUCESSO! Upload funcionou!")
            file_url = result.get('file', {}).get('permalink', 'N/A')
            print(f"   URL: {file_url}")
            print(f"\n🎉 Seu bot está funcionando corretamente!")
            print(f"   Agora faça o deploy: vercel --prod")
        else:
            error = result.get('error', 'desconhecido')
            print(f"\n❌ ERRO: {error}")
            
            if error == 'missing_scope':
                print(f"\n🔑 SOLUÇÃO:")
                print(f"   1. Vá em: https://api.slack.com/apps")
                print(f"   2. Selecione seu app")
                print(f"   3. OAuth & Permissions")
                print(f"   4. Bot Token Scopes → Adicione: files:write")
                print(f"   5. ⚠️ REINSTALE o app (botão no topo da página)")
                print(f"   6. Execute este script novamente")
            
            elif error == 'invalid_auth':
                print(f"\n🔐 SOLUÇÃO:")
                print(f"   1. Vá em: https://api.slack.com/apps")
                print(f"   2. OAuth & Permissions")
                print(f"   3. Copie o Bot User OAuth Token (xoxb-...)")
                print(f"   4. Execute: export SLACK_BOT_TOKEN='seu-token'")
                print(f"   5. Execute este script novamente")
            
            elif error == 'channel_not_found':
                print(f"\n📢 SOLUÇÃO:")
                print(f"   O ID do canal está incorreto: {channel_id}")
                print(f"   Verifique o ID na URL do Slack")
            
            elif error == 'not_in_channel':
                print(f"\n🚪 SOLUÇÃO:")
                print(f"   1. Vá no canal do Slack")
                print(f"   2. Digite: /invite @seu_bot")
                print(f"   3. Execute este script novamente")
            
            else:
                print(f"\n❓ Erro desconhecido")
                if 'needed' in result:
                    print(f"   Permissões necessárias: {result['needed']}")
                if 'provided' in result:
                    print(f"   Permissões fornecidas: {result['provided']}")
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"\n❌ Erro HTTP {e.code}:")
        print(error_body)
    
    except Exception as e:
        print(f"\n❌ Erro ao fazer upload: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("╔════════════════════════════════════════════╗")
    print("║   🧪 TESTE DE UPLOAD NO SLACK             ║")
    print("║   Verifica token e permissões             ║")
    print("╚════════════════════════════════════════════╝")
    print()
    
    try:
        test_slack_upload()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste cancelado pelo usuário")
    
    print("\n" + "="*50)
    print("Teste concluído!")
    print("="*50 + "\n")

