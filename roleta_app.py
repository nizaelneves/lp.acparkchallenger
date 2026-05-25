#!/usr/bin/env python3

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client
import os
import random

app = Flask(__name__, static_folder=".", static_url_path="")
# TODO: restringir CORS para domínio de produção antes do deploy público.
CORS(app)

load_dotenv(".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não encontrados no env.local")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ─── CONFIGURACAO DA ROLETA ─────────────────────────────────────────────────
SEGMENTS = [
    {"label": "PODE\nGANHAR",  "coupon": None,          "color": "#00c853", "textColor": "#fff"},
    {"label": "10%\nOFF",      "coupon": "DESCONTO10",   "color": "#00e676", "textColor": "#111"},
    {"label": "SEM\nSORTE :(", "coupon": None,          "color": "#00c853", "textColor": "#fff"},
    {"label": "7%\nOFF",       "coupon": "DESCONTO7",    "color": "#00e676", "textColor": "#111"},
    {"label": "25%\nOFF",      "coupon": "DESCONTO25",   "color": "#00c853", "textColor": "#fff"},
    {"label": "5%\nOFF",       "coupon": "DESCONTO5",    "color": "#00e676", "textColor": "#111"},
    {"label": "SEM\nSORTE :(", "coupon": None,          "color": "#00c853", "textColor": "#fff"},
    {"label": "20%\nOFF",      "coupon": "DESCONTO20",   "color": "#00e676", "textColor": "#111"},
]

# Pesos de probabilidade (maior = mais chance de cair nesse segmento)
WEIGHTS = [5, 20, 15, 25, 5, 25, 15, 20]

# ─────────────────────────────────────────────────────────────────────────────


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


def calculate_result(correct_answers, total_questions):
    score = correct_answers * 100

    # 12 acertos (1200 pts) → 2 giros especiais
    if correct_answers == 12:
        return {
            "score": score,
            "level_title": "Lenda Junina da Copa",
            "can_spin": True,
            "spin_type": "special",
            "spins_allowed": 2
        }

    # 7–11 acertos (700–1100 pts) → 1 giro normal
    if correct_answers >= 7:
        return {
            "score": score,
            "level_title": "Cabra Bom de Bola",
            "can_spin": True,
            "spin_type": "normal",
            "spins_allowed": 1
        }

    # Menos de 7 acertos → sem giro
    return {
        "score": score,
        "level_title": "Cabra da Peste em Treinamento",
        "can_spin": False,
        "spin_type": None,
        "spins_allowed": 0
    }

@app.route("/api/quiz-result", methods=["POST"])
def save_quiz_result():
    try:
        data = request.get_json()

        correct_answers = int(data.get("correct_answers", 0))
        total_questions = int(data.get("total_questions", 12))

        result = calculate_result(correct_answers, total_questions)

        response = (
            supabase
            .table("quiz_results")
            .insert({
              "score": result["score"],
              "correct_answers": correct_answers,
              "total_questions": total_questions,
              "level_title": result["level_title"],
              "can_spin": result["can_spin"],
              "spin_type": result["spin_type"],
              "spins_allowed": result["spins_allowed"],
              "spins_used": 0
})
            .execute()
        )

        saved_result = response.data[0]

        return jsonify({
              "success": True,
              "quiz_result_id": saved_result["id"],
              "score": result["score"],
              "level_title": result["level_title"],
              "can_spin": result["can_spin"],
              "spin_type": result["spin_type"],
              "spins_allowed": result["spins_allowed"],
              "spins_used": 0
})

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Erro ao salvar resultado do quiz",
            "error": str(error)
        }), 500

@app.route("/api/lead", methods=["POST"])
def save_lead():
    try:
        data = request.get_json()

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        quiz_result_id = data.get("quiz_result_id")
        consent_accepted = bool(data.get("consent_accepted", False))

        if not email:
            return jsonify({
                "success": False,
                "message": "E-mail é obrigatório"
            }), 400

        if not phone:
            return jsonify({
                "success": False,
                "message": "Telefone é obrigatório"
            }), 400

        if not quiz_result_id:
            return jsonify({
                "success": False,
                "message": "quiz_result_id é obrigatório"
            }), 400

        response = (
            supabase
            .table("leads")
            .insert({
                "name": name,
                "email": email,
                "phone": phone,
                "quiz_result_id": quiz_result_id,
                "consent_accepted": consent_accepted
            })
            .execute()
        )

        saved_lead = response.data[0]

        return jsonify({
            "success": True,
            "lead_id": saved_lead["id"]
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Erro ao salvar lead",
            "error": str(error)
        }), 500

@app.route("/api/spin", methods=["POST"])
def spin_roulette():
    try:
        data = request.get_json()

        lead_id = data.get("lead_id")
        quiz_result_id = data.get("quiz_result_id")

        if not lead_id:
            return jsonify({
                "success": False,
                "message": "lead_id é obrigatório"
            }), 400

        if not quiz_result_id:
            return jsonify({
                "success": False,
                "message": "quiz_result_id é obrigatório"
            }), 400

        # 1. Buscar resultado do quiz
        quiz_response = (
            supabase
            .table("quiz_results")
            .select("*")
            .eq("id", quiz_result_id)
            .single()
            .execute()
        )

        quiz_result = quiz_response.data

        if not quiz_result:
            return jsonify({
                "success": False,
                "message": "Resultado do quiz não encontrado"
            }), 404

        # 2. Verificar se pode girar
        if not quiz_result["can_spin"]:
            return jsonify({
                "success": False,
                "message": "Pontuação insuficiente para girar a roleta"
            }), 403

                # 3. Verificar quantos giros ainda restam
        spins_allowed = quiz_result.get("spins_allowed", 0)
        spins_used = quiz_result.get("spins_used", 0)

        if spins_used >= spins_allowed:
            return jsonify({
                "success": False,
                "message": "Você já usou todos os giros disponíveis"
            }), 403

        # 4. Buscar prêmios ativos
        rewards_response = (
            supabase
            .table("rewards")
            .select("*")
            .eq("is_active", True)
            .execute()
        )

        rewards = rewards_response.data

        if not rewards:
            return jsonify({
                "success": False,
                "message": "Nenhum prêmio ativo encontrado"
            }), 404

        # 5. Sorteio por peso
        weights = [reward["probability_weight"] for reward in rewards]
        selected_reward = random.choices(rewards, weights=weights, k=1)[0]

        # 6. Validade do cupom: 15 minutos
        valid_until = None

        if selected_reward.get("coupon_code"):
            from datetime import datetime, timedelta, timezone
            valid_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

        # 7. Salvar giro
        spin_response = (
            supabase
            .table("spins")
            .insert({
                "lead_id": lead_id,
                "quiz_result_id": quiz_result_id,
                "reward_id": selected_reward["id"],
                "coupon_code": selected_reward.get("coupon_code"),
                "valid_until": valid_until
            })
            .execute()
        )

        saved_spin = spin_response.data[0]

       # 8. Somar 1 giro usado
        new_spins_used = spins_used + 1

        (
        supabase
            .table("quiz_results")
            .update({
                "spins_used": new_spins_used,
                "spin_used": new_spins_used >= spins_allowed
            })
            .eq("id", quiz_result_id)
            .execute()
        )

        return jsonify({
            "success": True,
            "spin_id": saved_spin["id"],
            "reward_name": selected_reward["name"],
            "coupon_code": selected_reward.get("coupon_code"),
            "valid_until": valid_until,
            "spin_type": quiz_result.get("spin_type")
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Erro ao girar roleta",
            "error": str(error)
        }), 500

@app.route("/api/questions", methods=["GET"])
def get_questions():
    try:
        response = (
            supabase
            .table("questions")
            .select("*")
            .eq("is_active", True)
            .execute()
        )

        questions = response.data

        random.shuffle(questions)

        selected_questions = questions[:12]

        formatted_questions = []

        for q in selected_questions:
            formatted_questions.append({
                "id": q["id"],
                "question": q["question_text"],
                "correct": q["correct_option"],
                "options": [
                    q["option_a"],
                    q["option_b"],
                    q["option_c"],
                    q["option_d"]
                ],
                "category": q["category"],
                "difficulty": q["difficulty"]
            })

        return jsonify({
            "success": True,
            "questions": formatted_questions
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Erro ao buscar perguntas",
            "error": str(error)
        }), 500

if __name__ == '__main__':
    print()
    print("=" * 50)
    print("   QUIZ + ROLETA  -  v2.0")
    print("=" * 50)
    print("  App:    http://localhost:5000")
    print()
    print("  Para parar o servidor: Ctrl+C")
    print("=" * 50)
    print()
    app.run(debug=False, port=int(os.getenv("PORT", 5000)))
