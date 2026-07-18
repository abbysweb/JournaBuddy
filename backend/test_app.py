import os
import sys
import time
import io
# Dynamically resolve and append the backend folder to sys.path to guarantee clean imports
# regardless of current execution directory or developer environment.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources <<>> /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 23 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(Test) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n288\n%%EOF\n"

print("Testing health endpoint...")
with app.test_client() as client:
    resp = client.get('/api/health')
    print('Status code:', resp.status_code)
    print('JSON:', resp.get_json())
    
    print("\nTesting upload endpoint...")
    data = {'file': (io.BytesIO(MINIMAL_PDF), 'test.pdf')}
    resp = client.post('/api/upload', data=data, content_type='multipart/form-data')
    print('Upload Status:', resp.status_code)
    res_json = resp.get_json()
    print('Upload JSON:', res_json)
    
    if resp.status_code == 200:
        task_id = res_json.get('task_id')
        print(f"\nTesting status endpoint for task_id: {task_id}")
        
        # Poll a few times to see the mock progress
        for _ in range(8):
            status_resp = client.get(f'/api/status/{task_id}')
            print('Status JSON:', status_resp.get_json())
            time.sleep(2)
