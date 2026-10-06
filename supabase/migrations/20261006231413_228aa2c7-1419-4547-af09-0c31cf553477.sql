CREATE OR REPLACE FUNCTION public.log_security_event(
  _action text, _target_type text DEFAULT NULL, _target_id text DEFAULT NULL,
  _ip text DEFAULT NULL, _user_agent text DEFAULT NULL, _request_id text DEFAULT NULL)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public' AS $$
DECLARE _perm text; _result text; _reason text; _need text[]; _has boolean;
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'non authentifié'; END IF;

  IF _action = 'admin.access_denied' THEN
    IF _target_type IS DISTINCT FROM 'admin_section' THEN RAISE EXCEPTION 'cible non autorisée'; END IF;
    _need := CASE _target_id
      WHEN 'dashboard'    THEN NULL
      WHEN 'utilisateurs' THEN ARRAY['users.read']
      WHEN 'projets'      THEN ARRAY['projects.read_meta']
      WHEN 'gates'        THEN ARRAY['gates.read']
      WHEN 'moteurs'      THEN ARRAY['engines.read']
      WHEN 'usage'        THEN ARRAY['usage.read','costs.read']
      WHEN 'audit'        THEN ARRAY['audit.read']
      WHEN 'sante'        THEN ARRAY['health.read']
      WHEN 'securite'     THEN ARRAY['security.read']
      ELSE ARRAY['__invalid__'] END;
    IF _need = ARRAY['__invalid__'] THEN RAISE EXCEPTION 'section inconnue'; END IF;
    IF _need IS NULL THEN
      SELECT EXISTS (SELECT 1 FROM (SELECT DISTINCT permission FROM public.role_permissions) p
                     WHERE public.has_permission(auth.uid(), p.permission)) INTO _has;
    ELSE
      SELECT EXISTS (SELECT 1 FROM unnest(_need) p WHERE public.has_permission(auth.uid(), p)) INTO _has;
    END IF;
    -- has_permission renvoie déjà false si le compte est suspendu.
    IF _has THEN RETURN NULL; END IF;  -- accès réel : aucun faux refus
    _reason := CASE WHEN public.is_suspended(auth.uid()) THEN 'compte suspendu' ELSE 'permission manquante' END;
    RETURN public.log_admin_action('admin.access_denied', 'admin.access', 'admin_section', _target_id, _reason, 'denied',
                                   _ip, _user_agent, _request_id, NULL, NULL);
  END IF;

  _perm := CASE _action
    WHEN 'audit.list'   THEN 'audit.read'
    WHEN 'gates.decide' THEN 'gates.decide_on_behalf'
    ELSE NULL END;
  IF _perm IS NULL THEN RAISE EXCEPTION 'action non autorisée'; END IF;
  IF _target_type IS NOT NULL AND _target_type <> 'project' THEN RAISE EXCEPTION 'cible non autorisée'; END IF;
  IF _target_id IS NOT NULL AND _target_id !~ '^[0-9a-fA-F-]{36}$' THEN RAISE EXCEPTION 'identifiant invalide'; END IF;
  IF _action = 'gates.decide' THEN
    _result := 'denied';
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