-- 1) Plus aucun appel direct de log_admin_action par les comptes connectés.
REVOKE ALL ON FUNCTION public.log_admin_action(text,text,text,text,text,text,text,text,text,jsonb,jsonb) FROM PUBLIC, anon, authenticated;

-- 2) Seule porte d'entrée contrôlée : la base fixe permission, résultat, motif, avant/après.
CREATE OR REPLACE FUNCTION public.log_security_event(
  _action text, _target_type text DEFAULT NULL, _target_id text DEFAULT NULL,
  _ip text DEFAULT NULL, _user_agent text DEFAULT NULL, _request_id text DEFAULT NULL)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $$
DECLARE _perm text; _result text; _reason text;
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'non authentifié'; END IF;
  _perm := CASE _action
    WHEN 'audit.list'   THEN 'audit.read'
    WHEN 'gates.decide' THEN 'gates.decide_on_behalf'
    ELSE NULL END;
  IF _perm IS NULL THEN RAISE EXCEPTION 'action non autorisée'; END IF;
  IF _target_type IS NOT NULL AND _target_type <> 'project' THEN RAISE EXCEPTION 'cible non autorisée'; END IF;
  IF _target_id IS NOT NULL AND _target_id !~ '^[0-9a-fA-F-]{36}$' THEN RAISE EXCEPTION 'identifiant invalide'; END IF;
  IF _action = 'gates.decide' THEN
    _result := 'denied';  -- décider une Gate à la place du client est toujours refusé
  ELSIF public.has_permission(auth.uid(), _perm) THEN
    _result := 'allowed';
  ELSE
    _result := 'denied';
  END IF;
  IF public.is_suspended(auth.uid()) THEN _reason := 'compte suspendu'; _result := 'denied'; END IF;
  RETURN public.log_admin_action(_action, _perm, _target_type, _target_id, _reason, _result,
                                 _ip, _user_agent, _request_id, NULL, NULL);
END; $$;

REVOKE ALL ON FUNCTION public.log_security_event(text,text,text,text,text,text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.log_security_event(text,text,text,text,text,text) TO authenticated;