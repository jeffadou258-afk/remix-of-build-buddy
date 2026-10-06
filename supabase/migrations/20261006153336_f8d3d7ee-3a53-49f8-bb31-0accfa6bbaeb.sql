-- 1. Rôles
CREATE TYPE public.app_role AS ENUM ('user','support','ops','finance','admin','auditor');

CREATE TABLE public.user_roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role public.app_role NOT NULL,
  granted_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, role)
);
GRANT SELECT ON public.user_roles TO authenticated;
GRANT ALL ON public.user_roles TO service_role;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own roles read" ON public.user_roles FOR SELECT TO authenticated USING (auth.uid() = user_id);

-- 2. Matrice des permissions (§1.2 de la spécification)
CREATE TABLE public.role_permissions (
  role public.app_role NOT NULL,
  permission text NOT NULL,
  PRIMARY KEY (role, permission)
);
GRANT SELECT ON public.role_permissions TO authenticated;
GRANT ALL ON public.role_permissions TO service_role;
ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "matrix readable" ON public.role_permissions FOR SELECT TO authenticated USING (true);

INSERT INTO public.role_permissions (role, permission) VALUES
 ('support','users.read'),('finance','users.read'),('admin','users.read'),
 ('admin','users.suspend'),('admin','roles.manage'),
 ('support','projects.read_meta'),('ops','projects.read_meta'),('finance','projects.read_meta'),('admin','projects.read_meta'),
 ('support','projects.read_content'),('admin','projects.read_content'),
 ('admin','projects.archive'),
 ('support','activity.read'),('ops','activity.read'),('admin','activity.read'),('auditor','activity.read'),
 ('support','jobs.read'),('ops','jobs.read'),('admin','jobs.read'),
 ('support','jobs.retry'),('ops','jobs.retry'),('admin','jobs.retry'),
 ('ops','jobs.cancel'),('admin','jobs.cancel'),
 ('ops','engines.read'),('admin','engines.read'),
 ('ops','engines.toggle'),('admin','engines.toggle'),
 ('support','gates.read'),('ops','gates.read'),('admin','gates.read'),('auditor','gates.read'),
 ('ops','gates.unblock_technical'),('admin','gates.unblock_technical'),
 ('ops','usage.read'),('finance','usage.read'),('admin','usage.read'),
 ('finance','costs.read'),('admin','costs.read'),
 ('ops','providers.read'),('finance','providers.read'),('admin','providers.read'),
 ('admin','providers.manage'),
 ('support','errors.read'),('ops','errors.read'),('admin','errors.read'),
 ('support','health.read'),('ops','health.read'),('admin','health.read'),
 ('admin','audit.read'),('auditor','audit.read'),
 ('admin','security.read'),('auditor','security.read'),
 ('admin','security.manage');

-- 3. Statut de compte
CREATE TABLE public.account_status (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended')),
  reason text,
  updated_by uuid,
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.account_status TO authenticated;
GRANT ALL ON public.account_status TO service_role;
ALTER TABLE public.account_status ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own status read" ON public.account_status FOR SELECT TO authenticated USING (auth.uid() = user_id);

-- 4. Fonctions de vérification
CREATE OR REPLACE FUNCTION public.has_role(_user_id uuid, _role public.app_role)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (SELECT 1 FROM public.user_roles WHERE user_id = _user_id AND role = _role)
$$;

CREATE OR REPLACE FUNCTION public.is_suspended(_user_id uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (SELECT 1 FROM public.account_status WHERE user_id = _user_id AND status = 'suspended')
$$;

CREATE OR REPLACE FUNCTION public.has_permission(_user_id uuid, _perm text)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT _user_id IS NOT NULL
     AND NOT public.is_suspended(_user_id)
     AND EXISTS (SELECT 1 FROM public.user_roles ur JOIN public.role_permissions rp ON rp.role = ur.role
                 WHERE ur.user_id = _user_id AND rp.permission = _perm)
$$;

-- 5. Journal d'audit immuable
CREATE TABLE public.admin_audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  at timestamptz NOT NULL DEFAULT now(),
  actor_id uuid,
  actor_roles text[] NOT NULL DEFAULT '{}',
  action text NOT NULL,
  permission text,
  target_type text,
  target_id text,
  reason text,
  result text NOT NULL CHECK (result IN ('allowed','denied','error')),
  ip text,
  user_agent text,
  request_id text,
  before jsonb,
  after jsonb
);
GRANT SELECT ON public.admin_audit_log TO authenticated;
GRANT SELECT, INSERT ON public.admin_audit_log TO service_role;
ALTER TABLE public.admin_audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "audit read" ON public.admin_audit_log FOR SELECT TO authenticated USING (public.has_permission(auth.uid(), 'audit.read'));

CREATE OR REPLACE FUNCTION public.audit_log_immutable()
RETURNS trigger LANGUAGE plpgsql SET search_path = public AS $$
BEGIN RAISE EXCEPTION 'admin_audit_log est en ajout seulement'; END; $$;
CREATE TRIGGER audit_no_update BEFORE UPDATE OR DELETE ON public.admin_audit_log FOR EACH ROW EXECUTE FUNCTION public.audit_log_immutable();
CREATE TRIGGER audit_no_truncate BEFORE TRUNCATE ON public.admin_audit_log FOR EACH STATEMENT EXECUTE FUNCTION public.audit_log_immutable();

-- L'acteur et ses rôles sont toujours déterminés par la base, jamais fournis par l'appelant.
CREATE OR REPLACE FUNCTION public.log_admin_action(
  _action text, _permission text, _target_type text, _target_id text, _reason text, _result text,
  _ip text DEFAULT NULL, _user_agent text DEFAULT NULL, _request_id text DEFAULT NULL,
  _before jsonb DEFAULT NULL, _after jsonb DEFAULT NULL)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE _id uuid;
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'non authentifié'; END IF;
  INSERT INTO public.admin_audit_log (actor_id, actor_roles, action, permission, target_type, target_id, reason, result, ip, user_agent, request_id, before, after)
  VALUES (auth.uid(), COALESCE((SELECT array_agg(role::text) FROM public.user_roles WHERE user_id = auth.uid()), '{}'),
          left(_action,100), left(_permission,100), left(_target_type,50), left(_target_id,100), left(_reason,1000), _result,
          left(_ip,64), left(_user_agent,300), left(_request_id,100), _before, _after)
  RETURNING id INTO _id;
  RETURN _id;
END; $$;

-- 6. Accès audité au contenu d'un projet client
CREATE TABLE public.project_access_grants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  grantee_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  reason text NOT NULL CHECK (char_length(trim(reason)) >= 10),
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.project_access_grants TO authenticated;
GRANT ALL ON public.project_access_grants TO service_role;
ALTER TABLE public.project_access_grants ENABLE ROW LEVEL SECURITY;
CREATE POLICY "grantee or owner read" ON public.project_access_grants FOR SELECT TO authenticated
  USING (auth.uid() = grantee_id OR EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_id AND p.user_id = auth.uid()));

CREATE OR REPLACE FUNCTION public.request_project_access(_project_id uuid, _reason text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE _exp timestamptz := now() + interval '60 minutes';
BEGIN
  IF auth.uid() IS NULL THEN RETURN jsonb_build_object('ok',false,'error','unauthenticated'); END IF;
  IF NOT public.has_permission(auth.uid(), 'projects.read_content') THEN
    PERFORM public.log_admin_action('projects.request_content','projects.read_content','project',_project_id::text,_reason,'denied');
    RETURN jsonb_build_object('ok',false,'error','forbidden');
  END IF;
  IF _reason IS NULL OR char_length(trim(_reason)) < 10 THEN
    PERFORM public.log_admin_action('projects.request_content','projects.read_content','project',_project_id::text,_reason,'denied');
    RETURN jsonb_build_object('ok',false,'error','reason_required');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.projects WHERE id = _project_id) THEN
    RETURN jsonb_build_object('ok',false,'error','not_found');
  END IF;
  INSERT INTO public.project_access_grants (project_id, grantee_id, reason, expires_at) VALUES (_project_id, auth.uid(), trim(_reason), _exp);
  PERFORM public.log_admin_action('projects.request_content','projects.read_content','project',_project_id::text,_reason,'allowed');
  RETURN jsonb_build_object('ok',true,'expires_at',_exp);
END; $$;

CREATE OR REPLACE FUNCTION public.read_project_content(_project_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE _g record; _row jsonb;
BEGIN
  IF auth.uid() IS NULL THEN RETURN jsonb_build_object('ok',false,'error','unauthenticated'); END IF;
  SELECT * INTO _g FROM public.project_access_grants
   WHERE project_id = _project_id AND grantee_id = auth.uid() AND expires_at > now()
   ORDER BY expires_at DESC LIMIT 1;
  IF _g IS NULL OR NOT public.has_permission(auth.uid(), 'projects.read_content') THEN
    PERFORM public.log_admin_action('projects.read_content','projects.read_content','project',_project_id::text,NULL,'denied');
    RETURN jsonb_build_object('ok',false,'error','forbidden');
  END IF;
  SELECT jsonb_build_object('id',id,'title',title,'stage',stage,'messages',messages,'inputs',inputs,'building_model',building_model)
    INTO _row FROM public.projects WHERE id = _project_id;
  PERFORM public.log_admin_action('projects.read_content','projects.read_content','project',_project_id::text,_g.reason,'allowed');
  RETURN jsonb_build_object('ok',true,'project',_row,'grant_expires_at',_g.expires_at);
END; $$;

-- 7. Attribution / retrait de rôle (admin uniquement, jamais sur soi-même)
CREATE OR REPLACE FUNCTION public.grant_role(_target uuid, _role public.app_role, _reason text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE _before jsonb;
BEGIN
  IF auth.uid() IS NULL THEN RETURN jsonb_build_object('ok',false,'error','unauthenticated'); END IF;
  _before := COALESCE((SELECT to_jsonb(array_agg(role::text)) FROM public.user_roles WHERE user_id = _target), '[]'::jsonb);
  IF NOT public.has_permission(auth.uid(), 'roles.manage') OR _target = auth.uid() THEN
    PERFORM public.log_admin_action('roles.grant','roles.manage','user',_target::text,_reason,'denied',NULL,NULL,NULL,_before,NULL);
    RETURN jsonb_build_object('ok',false,'error', CASE WHEN _target = auth.uid() THEN 'self_grant_forbidden' ELSE 'forbidden' END);
  END IF;
  INSERT INTO public.user_roles (user_id, role, granted_by) VALUES (_target, _role, auth.uid()) ON CONFLICT DO NOTHING;
  PERFORM public.log_admin_action('roles.grant','roles.manage','user',_target::text,_reason,'allowed',NULL,NULL,NULL,_before,
    (SELECT to_jsonb(array_agg(role::text)) FROM public.user_roles WHERE user_id = _target));
  RETURN jsonb_build_object('ok',true);
END; $$;

CREATE OR REPLACE FUNCTION public.revoke_role(_target uuid, _role public.app_role, _reason text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE _before jsonb;
BEGIN
  IF auth.uid() IS NULL THEN RETURN jsonb_build_object('ok',false,'error','unauthenticated'); END IF;
  _before := COALESCE((SELECT to_jsonb(array_agg(role::text)) FROM public.user_roles WHERE user_id = _target), '[]'::jsonb);
  IF NOT public.has_permission(auth.uid(), 'roles.manage') OR _target = auth.uid() THEN
    PERFORM public.log_admin_action('roles.revoke','roles.manage','user',_target::text,_reason,'denied',NULL,NULL,NULL,_before,NULL);
    RETURN jsonb_build_object('ok',false,'error', CASE WHEN _target = auth.uid() THEN 'self_revoke_forbidden' ELSE 'forbidden' END);
  END IF;
  DELETE FROM public.user_roles WHERE user_id = _target AND role = _role;
  PERFORM public.log_admin_action('roles.revoke','roles.manage','user',_target::text,_reason,'allowed',NULL,NULL,NULL,_before,
    COALESCE((SELECT to_jsonb(array_agg(role::text)) FROM public.user_roles WHERE user_id = _target), '[]'::jsonb));
  RETURN jsonb_build_object('ok',true);
END; $$;

-- 8. Droits d'exécution : jamais anonymes
REVOKE ALL ON FUNCTION public.has_role(uuid, public.app_role) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.is_suspended(uuid) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.has_permission(uuid, text) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.log_admin_action(text,text,text,text,text,text,text,text,text,jsonb,jsonb) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.request_project_access(uuid, text) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.read_project_content(uuid) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.grant_role(uuid, public.app_role, text) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.revoke_role(uuid, public.app_role, text) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.audit_log_immutable() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.has_role(uuid, public.app_role) TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_suspended(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.has_permission(uuid, text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.log_admin_action(text,text,text,text,text,text,text,text,text,jsonb,jsonb) TO authenticated;
GRANT EXECUTE ON FUNCTION public.request_project_access(uuid, text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.read_project_content(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.grant_role(uuid, public.app_role, text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.revoke_role(uuid, public.app_role, text) TO authenticated;