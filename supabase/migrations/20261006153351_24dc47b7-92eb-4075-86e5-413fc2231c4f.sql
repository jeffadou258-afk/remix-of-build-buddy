CREATE OR REPLACE FUNCTION public.has_permission(_user_id uuid, _perm text)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT _user_id IS NOT NULL
     AND _user_id = auth.uid()
     AND NOT public.is_suspended(_user_id)
     AND EXISTS (SELECT 1 FROM public.user_roles ur JOIN public.role_permissions rp ON rp.role = ur.role
                 WHERE ur.user_id = _user_id AND rp.permission = _perm)
$$;
REVOKE EXECUTE ON FUNCTION public.has_role(uuid, public.app_role) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.is_suspended(uuid) FROM authenticated;