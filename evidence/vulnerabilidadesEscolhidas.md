Vulnerabilidade 1 — Autorização
Broken Object-Level Authorization (BOLA)

Um aluno autenticado consegue consultar as notas ou o perfil de outro aluno, alterando o student_id no pedido.
- Endpoint: GET /grades/<student_id>
- Endpoint adicional para variação: GET /students/<student_id>/profile
- Causa: ausência de verificação de permissões sobre o recurso específico.


Vulnerabilidade 2 — File access
Path Traversal / Arbitrary File Read

Um utilizador consegue tentar aceder a ficheiros fora da pasta materials, manipulando o parâmetro path.
- Endpoint: GET /files?path=<name>
- Causa: utilização de caminhos fornecidos pelo utilizador sem garantir que o ficheiro pertence à pasta autorizada.
